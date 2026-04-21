"""Spec tests for ../specs/mutexes.md.

Tests cover ATGETM (acquire) and ATRELM (release) through the full
TensixCoprocessor pipeline using raw instruction words (opcode 0xA0/0xA1)
or the TT_ATGETM/TT_ATRELM DSL helpers.

All tests exercise the functional behaviour of the mutex state machine.
Timing clauses (ATGETM.TIMING, ATRELM.TIMING) and the fairness guarantee
(MTX.FAIRNESS.ROUND_ROBIN) are marked testable: false in the ledger and
are not tested here.
"""

import pytest

from emu.tensix import TensixCoprocessor
from emu.dsl import TT_ATGETM, TT_ATRELM

from .conftest import spec


# ===========================================================================
# Fixture
# ===========================================================================

@pytest.fixture
def coprocessor():
  return TensixCoprocessor()


# ===========================================================================
# Initial state
# ===========================================================================

@spec("MTX.INDICES.INITIAL_STATE")
def test_all_mutexes_free_at_reset(coprocessor):
  """At reset, all mutex slots are free (None)."""
  t = coprocessor
  for i in range(5):
    assert t.mutexes[i] is None


@spec("MTX.INDICES.COUNT_4")
def test_mutex_array_size(coprocessor):
  """Mutex array is length 5 (indices 0-4; index 1 is invalid but reserved)."""
  assert len(coprocessor.mutexes) == 5


# ===========================================================================
# ATGETM — acquire
# ===========================================================================

@spec("MTX.ATGETM.ACQUIRE")
@pytest.mark.parametrize("idx", [0, 2, 3, 4])
def test_atgetm_acquires_free_mutex(coprocessor, idx):
  """ATGETM on a free valid mutex sets HeldBy = CurrentThread."""
  t = coprocessor
  word = int(TT_ATGETM(mutex_index=idx))
  t.push_instruction(0, word)
  t.step()
  assert t.mutexes[idx] == 0


@spec("MTX.ATGETM.BLOCKS_WHEN_HELD")
def test_atgetm_blocks_when_held_by_other_thread(coprocessor):
  """Thread 1's ATGETM is replayed while thread 0 holds the mutex."""
  t = coprocessor
  # T0 acquires mutex 0
  t.push_instruction(0, int(TT_ATGETM(mutex_index=0)))
  t.step()
  assert t.mutexes[0] == 0

  # T1 tries to acquire — should be replayed (blocked)
  t.push_instruction(1, int(TT_ATGETM(mutex_index=0)))
  t.step()
  assert t.mutexes[0] == 0        # T0 still holds it
  # T1's instruction was replayed (stashed in _replay_word or still in fifo)
  # The coprocessor keeps the instruction pending — T1 has not advanced.
  assert t.threads[1]._replay_word == int(TT_ATGETM(mutex_index=0))


@spec("MTX.ATGETM.REENTRANT")
def test_atgetm_reentrant_by_same_thread(coprocessor):
  """A thread can re-acquire a mutex it already holds without deadlock."""
  t = coprocessor
  word = int(TT_ATGETM(mutex_index=2))
  t.push_instruction(0, word)
  t.step()
  assert t.mutexes[2] == 0

  # Re-acquire by the same thread
  t.push_instruction(0, word)
  t.step()
  assert t.mutexes[2] == 0   # still held by T0, no deadlock


# ===========================================================================
# ATRELM — release
# ===========================================================================

@spec("MTX.ATRELM.RELEASE")
def test_atrelm_releases_owned_mutex(coprocessor):
  """ATRELM by the owning thread frees the mutex (sets to None)."""
  t = coprocessor
  t.push_instruction(0, int(TT_ATGETM(mutex_index=0)))
  t.step()
  assert t.mutexes[0] == 0

  t.push_instruction(0, int(TT_ATRELM(mutex_index=0)))
  t.step()
  assert t.mutexes[0] is None


@spec("MTX.ATRELM.NOOP_IF_NOT_HELD")
def test_atrelm_noop_on_unowned_mutex(coprocessor):
  """ATRELM on a mutex not held by the issuing thread has no effect."""
  t = coprocessor
  # Mutex 3 is free
  t.push_instruction(0, int(TT_ATRELM(mutex_index=3)))
  t.step()
  assert t.mutexes[3] is None   # still free — not an error


@spec("MTX.ATRELM.NOOP_IF_NOT_HELD")
def test_atrelm_noop_when_held_by_other(coprocessor):
  """ATRELM by a non-owner does not release the mutex."""
  t = coprocessor
  # T0 acquires mutex 4
  t.push_instruction(0, int(TT_ATGETM(mutex_index=4)))
  t.step()
  assert t.mutexes[4] == 0

  # T1 tries to release — no effect (T0 still holds it)
  t.push_instruction(1, int(TT_ATRELM(mutex_index=4)))
  t.step()
  assert t.mutexes[4] == 0


# ===========================================================================
# Acquire → Release → Re-acquire sequence
# ===========================================================================

@spec("MTX.ATGETM.ACQUIRE",
      "MTX.ATRELM.RELEASE",
      "MTX.ATGETM.BLOCKS_WHEN_HELD")
def test_acquire_release_allows_second_thread(coprocessor):
  """T0 acquires, releases; T1 was blocked but then acquires after the release."""
  t = coprocessor
  # T0 acquires mutex 0
  t.push_instruction(0, int(TT_ATGETM(mutex_index=0)))
  t.step()
  assert t.mutexes[0] == 0

  # T1 tries — blocked
  t.push_instruction(1, int(TT_ATGETM(mutex_index=0)))
  t.step()
  assert t.mutexes[0] == 0

  # T0 releases; T1 retries in the same step and succeeds
  t.push_instruction(0, int(TT_ATRELM(mutex_index=0)))
  t.step()
  assert t.mutexes[0] == 1   # T1 now holds it


# ===========================================================================
# Valid index set
# ===========================================================================

@spec("MTX.INDICES.VALID_SET")
@pytest.mark.parametrize("idx", [0, 2, 3, 4])
def test_valid_indices_are_acquirable(coprocessor, idx):
  """All valid mutex indices (0, 2, 3, 4) can be acquired."""
  t = coprocessor
  t.push_instruction(0, int(TT_ATGETM(mutex_index=idx)))
  t.step()
  assert t.mutexes[idx] == 0
