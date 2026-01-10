"""Tests for subprocess termination on run-evals cancellation.

These tests ensure that when the user cancels or exits the run-evals screen,
any running subprocess (inspect eval) is properly terminated and doesn't
continue running in the background.
"""

from __future__ import annotations

import os
import subprocess
import time
from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from open_telco.cli.screens.run_evals import RunEvalsScreen


class TestKillCurrentProcess:
    """Tests for the _kill_current_process method."""

    def test_kill_current_process_terminates_subprocess(self) -> None:
        """_kill_current_process should terminate running subprocess."""
        screen = RunEvalsScreen()
        screen.model = "test"

        # Start a real subprocess
        proc = subprocess.Popen(
            ["sleep", "60"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        screen._current_process = proc

        # Kill it
        screen._kill_current_process()

        # Verify it's dead
        assert proc.poll() is not None  # Returns exit code if terminated
        assert screen._current_process is None

    def test_kill_current_process_handles_none(self) -> None:
        """_kill_current_process should handle None process gracefully."""
        screen = RunEvalsScreen()
        screen.model = "test"
        screen._current_process = None

        # Should not raise
        screen._kill_current_process()

        assert screen._current_process is None

    def test_kill_current_process_handles_already_dead_process(self) -> None:
        """_kill_current_process should handle already-terminated process."""
        screen = RunEvalsScreen()
        screen.model = "test"

        # Start a process that exits immediately
        proc = subprocess.Popen(
            ["true"],  # exits immediately with 0
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        proc.wait()  # Wait for it to finish
        screen._current_process = proc

        # Should not raise
        screen._kill_current_process()

        assert screen._current_process is None

    def test_kill_with_stubborn_process(self) -> None:
        """Process that ignores SIGTERM should be killed with SIGKILL."""
        screen = RunEvalsScreen()
        screen.model = "test"

        mock_proc = MagicMock()
        # Simulate timeout on wait after terminate
        mock_proc.wait.side_effect = [subprocess.TimeoutExpired("sleep", 2), 0]
        screen._current_process = mock_proc

        screen._kill_current_process()

        mock_proc.terminate.assert_called_once()
        mock_proc.kill.assert_called_once()


class TestActionCancel:
    """Tests for the action_cancel method."""

    def test_action_cancel_sets_cancelled_flag(self) -> None:
        """action_cancel should set _cancelled to True."""
        screen = RunEvalsScreen()
        screen.model = "test"
        screen._cancelled = False

        # Mock app.pop_screen using patch on the property
        with patch.object(
            type(screen), "app", new_callable=PropertyMock
        ) as mock_app_prop:
            mock_app = MagicMock()
            mock_app_prop.return_value = mock_app

            screen.action_cancel()

            assert screen._cancelled is True
            mock_app.pop_screen.assert_called_once()

    def test_action_cancel_kills_running_process(self) -> None:
        """action_cancel should terminate running subprocess."""
        screen = RunEvalsScreen()
        screen.model = "test"

        # Create mock process
        mock_proc = MagicMock()
        mock_proc.wait.return_value = 0
        screen._current_process = mock_proc

        # Mock app
        with patch.object(
            type(screen), "app", new_callable=PropertyMock
        ) as mock_app_prop:
            mock_app = MagicMock()
            mock_app_prop.return_value = mock_app

            screen.action_cancel()

            mock_proc.terminate.assert_called_once()
            assert screen._current_process is None

    def test_action_cancel_without_process(self) -> None:
        """action_cancel should work when no process is running."""
        screen = RunEvalsScreen()
        screen.model = "test"
        screen._current_process = None

        # Mock app
        with patch.object(
            type(screen), "app", new_callable=PropertyMock
        ) as mock_app_prop:
            mock_app = MagicMock()
            mock_app_prop.return_value = mock_app

            # Should not raise
            screen.action_cancel()

            assert screen._cancelled is True
            mock_app.pop_screen.assert_called_once()


class TestOnUnmount:
    """Tests for the on_unmount method."""

    def test_on_unmount_kills_running_process(self) -> None:
        """on_unmount should terminate running subprocess."""
        screen = RunEvalsScreen()
        screen.model = "test"
        screen._animation_timer = None

        # Create mock process
        mock_proc = MagicMock()
        mock_proc.wait.return_value = 0
        screen._current_process = mock_proc

        screen.on_unmount()

        mock_proc.terminate.assert_called_once()

    def test_on_unmount_stops_timer(self) -> None:
        """on_unmount should stop animation timer."""
        screen = RunEvalsScreen()
        screen.model = "test"

        mock_timer = MagicMock()
        screen._animation_timer = mock_timer
        screen._current_process = None

        screen.on_unmount()

        mock_timer.stop.assert_called_once()
        assert screen._animation_timer is None

    def test_on_unmount_handles_all_cleanup(self) -> None:
        """on_unmount should clean up both timer and process."""
        screen = RunEvalsScreen()
        screen.model = "test"

        mock_timer = MagicMock()
        mock_proc = MagicMock()
        mock_proc.wait.return_value = 0

        screen._animation_timer = mock_timer
        screen._current_process = mock_proc

        screen.on_unmount()

        mock_timer.stop.assert_called_once()
        mock_proc.terminate.assert_called_once()
        assert screen._animation_timer is None
        assert screen._current_process is None


class TestCancelledFlag:
    """Tests for the _cancelled flag behavior."""

    def test_cancelled_flag_prevents_mini_test(self) -> None:
        """_run_mini_test should return immediately if cancelled."""
        screen = RunEvalsScreen()
        screen.model = "test"
        screen._cancelled = True

        result = screen._run_mini_test()

        assert result["passed"] is False
        assert result["error"] == "cancelled"

    def test_cancelled_flag_initially_false(self) -> None:
        """_cancelled should be False on initialization."""
        screen = RunEvalsScreen()
        screen.model = "test"

        assert screen._cancelled is False

    def test_current_process_initially_none(self) -> None:
        """_current_process should be None on initialization."""
        screen = RunEvalsScreen()
        screen.model = "test"

        assert screen._current_process is None


class TestOrphanProcessPrevention:
    """Integration tests for orphan process prevention."""

    def test_no_orphan_process_after_cancel(self) -> None:
        """Verify no orphan processes remain after cancel."""
        screen = RunEvalsScreen()
        screen.model = "test"

        # Start a subprocess
        proc = subprocess.Popen(
            ["sleep", "60"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        pid = proc.pid
        screen._current_process = proc

        # Mock app
        with patch.object(
            type(screen), "app", new_callable=PropertyMock
        ) as mock_app_prop:
            mock_app = MagicMock()
            mock_app_prop.return_value = mock_app

            # Cancel
            screen.action_cancel()

        # Wait a moment for cleanup
        time.sleep(0.1)

        # Check process is gone
        try:
            os.kill(pid, 0)  # Check if process exists (signal 0 = check only)
            pytest.fail(f"Process {pid} still running after cancel")
        except ProcessLookupError:
            pass  # Expected - process is gone

    def test_no_orphan_process_after_unmount(self) -> None:
        """Verify no orphan processes remain after unmount."""
        screen = RunEvalsScreen()
        screen.model = "test"
        screen._animation_timer = None

        # Start a subprocess
        proc = subprocess.Popen(
            ["sleep", "60"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        pid = proc.pid
        screen._current_process = proc

        # Unmount
        screen.on_unmount()

        # Wait a moment for cleanup
        time.sleep(0.1)

        # Check process is gone
        try:
            os.kill(pid, 0)
            pytest.fail(f"Process {pid} still running after unmount")
        except ProcessLookupError:
            pass  # Expected

    def test_multiple_cancels_are_safe(self) -> None:
        """Multiple cancel calls should be safe (idempotent)."""
        screen = RunEvalsScreen()
        screen.model = "test"

        # Start a subprocess
        proc = subprocess.Popen(
            ["sleep", "60"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        screen._current_process = proc

        # Mock app
        with patch.object(
            type(screen), "app", new_callable=PropertyMock
        ) as mock_app_prop:
            mock_app = MagicMock()
            mock_app_prop.return_value = mock_app

            # Cancel multiple times
            screen.action_cancel()
            screen.action_cancel()
            screen.action_cancel()

        # Should not raise and process should be gone
        assert screen._current_process is None
        assert screen._cancelled is True
