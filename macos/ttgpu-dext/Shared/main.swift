// TTGPU.app: activates/deactivates the driver extension, and hosts the PCI server (server.c) that pci_macos.py talks to.
import Foundation
import SystemExtensions

final class Delegate: NSObject, OSSystemExtensionRequestDelegate {
  func requestNeedsUserApproval(_ r: OSSystemExtensionRequest) {
    print("Waiting for approval: System Settings > General > Login Items & Extensions > Driver Extensions > TTGPU")
  }
  func request(_ r: OSSystemExtensionRequest, didFinishWithResult result: OSSystemExtensionRequest.Result) {
    print(result == .willCompleteAfterReboot ? "Done; completes after reboot." : "Done.")
    exit(0)
  }
  func request(_ r: OSSystemExtensionRequest, didFailWithError error: Error) {
    print("Failed: \(error.localizedDescription) (code \((error as NSError).code))")
    exit(3)
  }
  func request(_ r: OSSystemExtensionRequest, actionForReplacingExtension old: OSSystemExtensionProperties,
               withExtension new: OSSystemExtensionProperties) -> OSSystemExtensionRequest.ReplacementAction {
    print("Replacing build \(old.bundleVersion) with \(new.bundleVersion)")
    return .replace
  }
}

let args = CommandLine.arguments, dextID = "com.boopapps.ttgpu.driver", delegate = Delegate()
switch (args.count > 1 ? args[1] : "", args.count) {
case ("server", 3):
  exit(run_server(args[2]) == 0 ? 0 : 3)
case ("install", 2), ("uninstall", 2):
  let req = args[1] == "install"
    ? OSSystemExtensionRequest.activationRequest(forExtensionWithIdentifier: dextID, queue: .main)
    : OSSystemExtensionRequest.deactivationRequest(forExtensionWithIdentifier: dextID, queue: .main)
  req.delegate = delegate
  OSSystemExtensionManager.shared.submitRequest(req)
  dispatchMain()
default:
  print("usage: TTGPU install | uninstall | server <socket>")
  exit(2)
}
