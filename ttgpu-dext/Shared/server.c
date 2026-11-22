#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <unistd.h>
#include <pthread.h>
#include <signal.h>
#include <sys/file.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <errno.h>
#include <dispatch/dispatch.h>
#include <CoreFoundation/CoreFoundation.h>
#include <IOKit/IOKitLib.h>
#include <IOKit/IOMessage.h>
#include <IOKit/pwr_mgt/IOPMLib.h>
#include <mach/mach.h>

enum {
  CMD_PROBE = 0,
  CMD_MAP_BAR = 1,
  CMD_MAP_SYSMEM_FD = 2,
  CMD_CFG_READ = 3,
  CMD_CFG_WRITE = 4,
  CMD_RESET = 5,
  CMD_MMIO_READ = 6,
  CMD_MMIO_WRITE = 7,
  CMD_RESIZE_BAR = 11,
  CMD_PING = 12,
  CMD_NOC_READ32 = 13,
};
enum { RESP_OK = 0, RESP_ERR = 1 };
enum { SEL_READ_CFG = 0, SEL_WRITE_CFG = 1, SEL_RESET = 2, SEL_PREPARE_DMA = 3 };

typedef struct { uint8_t cmd; uint32_t dev_id, bar; uint64_t arg0, arg1, arg2; } __attribute__((packed)) request_t;
typedef struct { uint8_t status; uint64_t resp0, resp1; } __attribute__((packed)) response_t;

#define BULK_BUF_SIZE (4 << 20)
#define MAX_CLIENTS 8
#define MAX_BARS 6
#define MAX_SYSMEM 128
#define MAX_SYSMEM_SIZE (1ull << 40)
#define DMA_TABLE_SIZE 8192
#define DMA_BAR 2
#define TLB_REGS 0x1FC00000ull
#define TLB_REG_SIZE 12
#define TLB_SIZE (1ull << 21)
#define NOC_TLB 200
#define PCI_COMMAND 0x04
#define PCI_COMMAND_MEMORY 0x2
#define PCI_COMMAND_MASTER 0x4

typedef struct {
  int used, fd, dma;
  io_connect_t conn;
  uint8_t *bulk;
  char error[256];
  struct { mach_vm_address_t addr; mach_vm_size_t size; } bars[MAX_BARS];
  struct { void *addr; size_t size; int fd; } sysmem[MAX_SYSMEM];
  int sysmem_count;
} client_t;

static pthread_mutex_t g_lock = PTHREAD_MUTEX_INITIALIZER;
static client_t g_clients[MAX_CLIENTS];
static client_t *g_resetting;
static int g_dma_clients;
static io_connect_t g_pm_root = IO_OBJECT_NULL;

static int recvall(int fd, void *buf, size_t len) {
  for (size_t off = 0; off < len;) {
    ssize_t r = recv(fd, (uint8_t *)buf + off, len - off, 0);
    if (r < 0 && errno == EINTR) continue;
    if (r <= 0) return -1;
    off += r;
  }
  return 0;
}

static int sendall(int fd, const void *buf, size_t len) {
  for (size_t off = 0; off < len;) {
    ssize_t r = send(fd, (const uint8_t *)buf + off, len - off, 0);
    if (r < 0 && errno == EINTR) continue;
    if (r <= 0) return -1;
    off += r;
  }
  return 0;
}

static void mmio_copy(void *dst, const void *src, size_t len) {
  volatile uint32_t *d = dst;
  const volatile uint32_t *s = src;
  for (size_t i = 0; i < len / 4; i++) d[i] = s[i];
}

static int send_response(int fd, const response_t *resp, int send_fd) {
  if (send_fd < 0) return sendall(fd, resp, sizeof(*resp));
  char cmsgbuf[CMSG_SPACE(sizeof(int))];
  struct iovec iov = {(void *)resp, sizeof(*resp)};
  struct msghdr msg = {.msg_iov = &iov, .msg_iovlen = 1, .msg_control = cmsgbuf, .msg_controllen = sizeof(cmsgbuf)};
  struct cmsghdr *cmsg = CMSG_FIRSTHDR(&msg);
  *cmsg = (struct cmsghdr){.cmsg_level = SOL_SOCKET, .cmsg_type = SCM_RIGHTS, .cmsg_len = CMSG_LEN(sizeof(int))};
  memcpy(CMSG_DATA(cmsg), &send_fd, sizeof(int));
  ssize_t r;
  while ((r = sendmsg(fd, &msg, 0)) < 0 && errno == EINTR) {}
  if (r <= 0) return -1;
  return r == sizeof(*resp) ? 0 : sendall(fd, (const uint8_t *)resp + r, sizeof(*resp) - r);
}

static int send_error(int fd, const char *msg) {
  response_t resp = {.status = RESP_ERR, .resp0 = strlen(msg)};
  return send_response(fd, &resp, -1) || sendall(fd, msg, strlen(msg));
}

static int dext_call(client_t *c, uint32_t sel, const uint64_t *in, uint32_t in_cnt, uint64_t *out_val) {
  uint64_t out[1] = {0};
  uint32_t out_cnt = out_val ? 1 : 0;
  kern_return_t kr = IOConnectCallScalarMethod(c->conn, sel, in, in_cnt, out, &out_cnt);
  if (kr != KERN_SUCCESS) { snprintf(c->error, sizeof(c->error), "dext call %u failed: 0x%x", sel, kr); return -1; }
  if (out_val) *out_val = out[0];
  return 0;
}

static int cfg_read(client_t *c, uint32_t off, uint32_t size, uint64_t *val) { uint64_t in[2] = {off, size}; return dext_call(c, SEL_READ_CFG, in, 2, val); }
static int cfg_write(client_t *c, uint32_t off, uint32_t size, uint64_t val) { uint64_t in[3] = {off, size, val}; return dext_call(c, SEL_WRITE_CFG, in, 3, NULL); }

static void set_bus_master(client_t *c, int on) {
  uint64_t cmd;
  if (cfg_read(c, PCI_COMMAND, 2, &cmd)) return;
  cmd = on ? (cmd | PCI_COMMAND_MEMORY | PCI_COMMAND_MASTER) : (cmd & ~(uint64_t)PCI_COMMAND_MASTER);
  cfg_write(c, PCI_COMMAND, 2, cmd);
}

static void dma_attach(client_t *c) {
  if (c->dma) return;
  c->dma = 1;
  if (g_dma_clients++ == 0) set_bus_master(c, 1);
}

static void dma_detach(client_t *c) {
  if (!c->dma) return;
  c->dma = 0;
  if (--g_dma_clients == 0 && c->conn != IO_OBJECT_NULL) set_bus_master(c, 0);
}

static void release_client(client_t *c) {
  for (int i = 0; i < MAX_BARS; i++)
    if (c->bars[i].addr) { IOConnectUnmapMemory64(c->conn, i, mach_task_self(), c->bars[i].addr); c->bars[i].addr = 0; }
  if (c->conn != IO_OBJECT_NULL) { IOServiceClose(c->conn); c->conn = IO_OBJECT_NULL; }
  for (int i = 0; i < c->sysmem_count; i++) { munmap(c->sysmem[i].addr, c->sysmem[i].size); close(c->sysmem[i].fd); }
  c->sysmem_count = 0;
}

static void revoke_all(const char *why) {
  fprintf(stderr, "ttgpu server: %s, releasing the device\n", why);
  for (int i = 0; i < MAX_CLIENTS; i++)
    if (g_clients[i].used && g_clients[i].conn != IO_OBJECT_NULL) { set_bus_master(&g_clients[i], 0); break; }
  for (int i = 0; i < MAX_CLIENTS; i++) if (g_clients[i].used) release_client(&g_clients[i]);
}

static void on_service_interest(void *refcon, io_service_t svc, uint32_t msg, void *arg) {
  if (msg != kIOMessageServiceIsTerminated) return;
  pthread_mutex_lock(&g_lock);
  revoke_all("device terminated");
  _exit(0);
}

static void on_system_power(void *refcon, io_service_t svc, uint32_t msg, void *arg) {
  switch (msg) {
  case kIOMessageCanSystemSleep: IOAllowPowerChange(g_pm_root, (intptr_t)arg); break;
  case kIOMessageSystemWillSleep:
    pthread_mutex_lock(&g_lock);
    revoke_all("system sleep");
    IOAllowPowerChange(g_pm_root, (intptr_t)arg);
    _exit(0);
  }
}

static void watch_power(void) {
  IONotificationPortRef port;
  io_object_t notifier;
  g_pm_root = IORegisterForSystemPower(NULL, &port, on_system_power, &notifier);
  if (g_pm_root == IO_OBJECT_NULL) { fprintf(stderr, "ttgpu server: IORegisterForSystemPower failed\n"); return; }
  IONotificationPortSetDispatchQueue(port, dispatch_queue_create("ttgpu.power", DISPATCH_QUEUE_SERIAL));
}

static io_connect_t open_device(const char **err) {
  static io_object_t notif;
  static IONotificationPortRef port;
  io_service_t svc = IOServiceGetMatchingService(kIOMainPortDefault, IOServiceNameMatching("ttgpu"));
  if (!svc) { *err = "no ttgpu device: is the card connected and the TTGPU driver enabled? (systemextensionsctl list; ioreg -n ttgpu)"; return IO_OBJECT_NULL; }
  if (!notif) {
    port = IONotificationPortCreate(kIOMainPortDefault);
    IONotificationPortSetDispatchQueue(port, dispatch_queue_create("ttgpu.device", DISPATCH_QUEUE_SERIAL));
    IOServiceAddInterestNotification(port, svc, kIOGeneralInterest, on_service_interest, NULL, &notif);
  }
  io_connect_t conn = IO_OBJECT_NULL;
  kern_return_t kr = IOServiceOpen(svc, mach_task_self(), 0, &conn);
  IOObjectRelease(svc);
  if (kr != KERN_SUCCESS) { *err = "IOServiceOpen on the ttgpu driver failed"; return IO_OBJECT_NULL; }
  return conn;
}

static int map_bar(client_t *c, uint32_t bar, response_t *resp) {
  if (bar >= MAX_BARS) { snprintf(c->error, sizeof(c->error), "no BAR%u", bar); return -1; }
  if (!c->bars[bar].addr) {
    kern_return_t kr = IOConnectMapMemory64(c->conn, bar, mach_task_self(), &c->bars[bar].addr, &c->bars[bar].size, kIOMapAnywhere);
    if (kr != KERN_SUCCESS) { c->bars[bar].addr = 0; snprintf(c->error, sizeof(c->error), "mapping BAR%u failed: 0x%x", bar, kr); return -1; }
  }
  if (bar == DMA_BAR) dma_attach(c);
  resp->resp0 = c->bars[bar].addr;
  resp->resp1 = c->bars[bar].size;
  return 0;
}

static int map_sysmem_fd(client_t *c, uint64_t size, response_t *resp, int *out_fd) {
  if (c->sysmem_count >= MAX_SYSMEM) { snprintf(c->error, sizeof(c->error), "too many DMA buffers"); return -1; }
  if (size > MAX_SYSMEM_SIZE) { snprintf(c->error, sizeof(c->error), "DMA buffer of %#llx bytes is too large", size); return -1; }
  size_t alloc_sz = (size + 0x3fff) & ~(size_t)0x3fff;
  if (alloc_sz < 0x4000) alloc_sz = 0x4000;
  int fd = -1;
  void *ptr = MAP_FAILED;
  char name[32];
  snprintf(name, sizeof(name), "/ttgpu_%d_%td_%d", getpid(), c - g_clients, c->sysmem_count);
  shm_unlink(name);
  if ((fd = shm_open(name, O_CREAT | O_RDWR | O_EXCL, 0600)) < 0) goto fail;
  shm_unlink(name);
  if (ftruncate(fd, alloc_sz) < 0) goto fail;
  if ((ptr = mmap(NULL, alloc_sz, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0)) == MAP_FAILED) goto fail;

  uint8_t table[DMA_TABLE_SIZE] = {0};
  size_t table_sz = sizeof(table);
  kern_return_t kr = IOConnectCallStructMethod(c->conn, SEL_PREPARE_DMA, ptr, alloc_sz, table, &table_sz);
  if (kr != KERN_SUCCESS) { snprintf(c->error, sizeof(c->error), "pinning %zu bytes for DMA failed: 0x%x", alloc_sz, kr); goto fail; }
  memcpy(ptr, table, alloc_sz < table_sz ? alloc_sz : table_sz);

  int idx = c->sysmem_count++;
  c->sysmem[idx].addr = ptr;
  c->sysmem[idx].size = alloc_sz;
  c->sysmem[idx].fd = fd;
  dma_attach(c);
  *resp = (response_t){.resp0 = alloc_sz, .resp1 = idx};
  *out_fd = fd;
  return 0;

fail:
  if (!c->error[0]) snprintf(c->error, sizeof(c->error), "allocating %zu bytes of shared memory failed: %s", alloc_sz, strerror(errno));
  if (ptr != MAP_FAILED) munmap(ptr, alloc_sz);
  if (fd >= 0) close(fd);
  return -1;
}

static int mmio_ok(client_t *c, uint32_t bar, uint64_t off, uint64_t sz) {
  if (g_resetting && g_resetting != c) { snprintf(c->error, sizeof(c->error), "the card is being reset"); return 0; }
  if (bar < MAX_BARS && c->bars[bar].addr && sz <= BULK_BUF_SIZE && !(off & 3) && !(sz & 3) && off <= c->bars[bar].size && sz <= c->bars[bar].size - off) return 1;
  snprintf(c->error, sizeof(c->error), "MMIO BAR%u [%#llx, +%#llx) unaligned, out of range or not mapped", bar, off, sz);
  return 0;
}

static int noc_read32(client_t *c, uint64_t addr, uint64_t xy, uint64_t *val) {
  uint64_t base = addr & ~(TLB_SIZE - 1), x = xy & 63, y = xy >> 8 & 63;
  if (!mmio_ok(c, 0, TLB_REGS + NOC_TLB * TLB_REG_SIZE, 12) || !mmio_ok(c, 0, NOC_TLB * TLB_SIZE + (addr - base), 4)) return -1;
  unsigned __int128 v = base >> 21 | (unsigned __int128)x << 43 | (unsigned __int128)y << 49 | (unsigned __int128)x << 55 |
                        (unsigned __int128)y << 61 | (unsigned __int128)1 << 70;
  volatile uint32_t *reg = (volatile uint32_t *)(c->bars[0].addr + TLB_REGS + NOC_TLB * TLB_REG_SIZE);
  for (int i = 0; i < 3; i++) reg[i] = (uint32_t)(v >> 32 * i);
  *val = *(volatile uint32_t *)(c->bars[0].addr + NOC_TLB * TLB_SIZE + (addr - base));
  return 0;
}

static void serve(client_t *c) {
  int fd = c->fd;
  request_t req;
  for (;;) {
    if (recvall(fd, &req, sizeof(req))) return;
    response_t resp = {0};
    int send_fd = -1, ok = 1;

    if (req.cmd == CMD_MMIO_WRITE) {
      int fits = req.arg1 <= BULK_BUF_SIZE;
      for (uint64_t left = req.arg1; left;) {
        uint64_t n = left < BULK_BUF_SIZE ? left : BULK_BUF_SIZE;
        if (recvall(fd, c->bulk, n)) return;
        left -= n;
      }
      pthread_mutex_lock(&g_lock);
      if (!fits) snprintf(c->error, sizeof(c->error), "MMIO write of %#llx bytes is larger than %#x", req.arg1, BULK_BUF_SIZE);
      else if (!c->error[0] && mmio_ok(c, req.bar, req.arg0, req.arg1)) mmio_copy((void *)(c->bars[req.bar].addr + req.arg0), c->bulk, req.arg1);
      pthread_mutex_unlock(&g_lock);
      continue;
    }

    pthread_mutex_lock(&g_lock);
    if (c->error[0]) ok = 0;
    else switch (req.cmd) {
    case CMD_MAP_BAR: ok = !map_bar(c, req.bar, &resp); break;
    case CMD_MAP_SYSMEM_FD: ok = !map_sysmem_fd(c, req.arg0, &resp, &send_fd); break;
    case CMD_CFG_READ: { uint64_t v = 0; ok = !cfg_read(c, (uint32_t)req.arg0, (uint32_t)req.arg1, &v); resp.resp0 = v; break; }
    case CMD_CFG_WRITE: ok = !cfg_write(c, (uint32_t)req.arg0, (uint32_t)req.arg1, req.arg2); break;
    case CMD_RESET:
      if (g_resetting && g_resetting != c) { ok = 0; snprintf(c->error, sizeof(c->error), "the card is being reset"); break; }
      g_resetting = c;
      ok = !dext_call(c, SEL_RESET, NULL, 0, NULL);
      break;
    case CMD_MMIO_READ:
      if ((ok = mmio_ok(c, req.bar, req.arg0, req.arg1))) {
        mmio_copy(c->bulk, (void *)(c->bars[req.bar].addr + req.arg0), req.arg1);
        resp.resp0 = req.arg1;
      }
      break;
    case CMD_NOC_READ32: { uint64_t v = 0; ok = !noc_read32(c, req.arg0, req.arg1, &v); resp.resp0 = v; break; }
    case CMD_RESIZE_BAR: case CMD_PING: break;
    default: ok = 0; snprintf(c->error, sizeof(c->error), "unknown command %u", req.cmd);
    }
    char err[sizeof(c->error)];
    strlcpy(err, c->error, sizeof(err));
    c->error[0] = 0;
    pthread_mutex_unlock(&g_lock);

    if (!ok) { if (send_error(fd, err[0] ? err : "failed")) return; continue; }
    if (send_response(fd, &resp, send_fd)) return;
    if (req.cmd == CMD_MMIO_READ && sendall(fd, c->bulk, req.arg1)) return;
  }
}

static void *client_thread(void *arg) {
  client_t *c = arg;
  int bufsize = 8 << 20;
  setsockopt(c->fd, SOL_SOCKET, SO_SNDBUF, &bufsize, sizeof(bufsize));
  setsockopt(c->fd, SOL_SOCKET, SO_RCVBUF, &bufsize, sizeof(bufsize));

  const char *open_err = "out of memory";
  pthread_mutex_lock(&g_lock);
  c->bulk = malloc(BULK_BUF_SIZE);
  c->conn = c->bulk ? open_device(&open_err) : IO_OBJECT_NULL;
  pthread_mutex_unlock(&g_lock);

  if (c->conn == IO_OBJECT_NULL) send_error(c->fd, open_err);
  else serve(c);

  pthread_mutex_lock(&g_lock);
  dma_detach(c);
  if (g_resetting == c) g_resetting = NULL;
  release_client(c);
  close(c->fd);
  free(c->bulk);
  memset(c, 0, sizeof(*c));
  pthread_mutex_unlock(&g_lock);
  return NULL;
}

int run_server(const char *sock_path) {
  signal(SIGPIPE, SIG_IGN);
  char lock_path[sizeof(((struct sockaddr_un *)0)->sun_path) + 8];
  snprintf(lock_path, sizeof(lock_path), "%s.lock", sock_path);
  int lock_fd = open(lock_path, O_RDWR | O_CREAT | O_CLOEXEC, 0600);
  if (lock_fd < 0) { perror("open lock"); return 1; }
  if (flock(lock_fd, LOCK_EX | LOCK_NB) < 0) {
    if (errno == EWOULDBLOCK) { fprintf(stderr, "ttgpu server: already running on %s\n", sock_path); return 0; }
    perror("flock");
    return 1;
  }
  watch_power();
  int server_fd = socket(AF_UNIX, SOCK_STREAM, 0);
  if (server_fd < 0) { perror("socket"); return 1; }
  struct sockaddr_un addr = {.sun_family = AF_UNIX};
  strncpy(addr.sun_path, sock_path, sizeof(addr.sun_path) - 1);
  unlink(sock_path);
  if (bind(server_fd, (struct sockaddr *)&addr, sizeof(addr)) < 0) { perror("bind"); close(server_fd); return 1; }
  chmod(sock_path, 0600);
  if (listen(server_fd, MAX_CLIENTS) < 0) { perror("listen"); close(server_fd); return 1; }
  fprintf(stderr, "ttgpu server: listening on %s\n", sock_path);

  for (;;) {
    int fd = accept(server_fd, NULL, NULL);
    if (fd < 0) { if (errno == EINTR) continue; perror("accept"); break; }
    pthread_mutex_lock(&g_lock);
    client_t *c = NULL;
    for (int i = 0; i < MAX_CLIENTS && !c; i++) if (!g_clients[i].used) c = &g_clients[i];
    if (c) { c->used = 1; c->fd = fd; }
    pthread_mutex_unlock(&g_lock);
    if (!c) { send_error(fd, "too many clients"); close(fd); continue; }
    pthread_t t;
    if (pthread_create(&t, NULL, client_thread, c)) { pthread_mutex_lock(&g_lock); memset(c, 0, sizeof(*c)); pthread_mutex_unlock(&g_lock); close(fd); continue; }
    pthread_detach(t);
  }
  close(server_fd);
  unlink(sock_path);
  return 0;
}
