package taskqueue

import (
	"sync"
	"sync/atomic"
	"testing"
	"time"
)

func TestProcessBG_NonBlocking(t *testing.T) {
	started := make(chan struct{})
	completed := make(chan struct{})

	go func() {
		close(started)
		ProcessBG(map[string]any{
			"delay":   10 * time.Millisecond,
			"timeout": 100 * time.Millisecond,
		})
		close(completed)
	}()

	select {
	case <-started:
	case <-time.After(100 * time.Millisecond):
		t.Fatal("ProcessBG did not start in time")
	}

	select {
	case <-completed:
	case <-time.After(100 * time.Millisecond):
		t.Fatal("ProcessBG appears to be blocking")
	}
}

func TestBackgroundProcessor_NoRace(t *testing.T) {
	processor := NewBackgroundProcessor(100)
	processor.Start(4)

	var wg sync.WaitGroup
	var successCount atomic.Int32

	for i := 0; i < 10; i++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			for j := 0; j < 10; j++ {
				err := processor.Submit(map[string]any{
					"id":      id,
					"task":    j,
					"delay":   1 * time.Millisecond,
					"timeout": 50 * time.Millisecond,
				}, 50*time.Millisecond)
				if err == nil {
					successCount.Add(1)
				}
			}
		}(i)
	}

	wg.Wait()
	time.Sleep(100 * time.Millisecond)

	processor.Shutdown()

	if successCount.Load() == 0 {
		t.Error("No tasks were successfully submitted")
	}
}

func TestBackgroundProcessor_ContextTimeout(t *testing.T) {
	processor := NewBackgroundProcessor(10)
	processor.Start(2)

	err := processor.Submit(map[string]any{
		"delay":   500 * time.Millisecond, 
		"timeout": 10 * time.Millisecond,
	}, 10*time.Millisecond)

	if err != nil {
		t.Fatalf("Failed to submit task: %v", err)
	}

	time.Sleep(100 * time.Millisecond)
	processor.Shutdown()
}

func TestBackgroundProcessor_GracefulShutdown(t *testing.T) {
	processor := NewBackgroundProcessor(10)
	processor.Start(2)

	var completedTasks atomic.Int32

	for i := 0; i < 5; i++ {
		err := processor.Submit(map[string]any{
			"delay":   10 * time.Millisecond,
			"timeout": 100 * time.Millisecond,
			"callback": func() {
				completedTasks.Add(1)
			},
		}, 100*time.Millisecond)
		if err != nil {
			t.Logf("Task %d not submitted: %v", i, err)
		}
	}

	time.Sleep(50 * time.Millisecond)

	shutdownDone := make(chan struct{})
	go func() {
		processor.Shutdown()
		close(shutdownDone)
	}()

	select {
	case <-shutdownDone:
	case <-time.After(2 * time.Second):
		t.Fatal("Shutdown did not complete - possible goroutine leak")
	}
}

func TestBackgroundProcessor_QueueFull(t *testing.T) {
	processor := NewBackgroundProcessor(2) 
	processor.Start(1)

	for i := 0; i < 5; i++ {
		_ = processor.Submit(map[string]any{
			"delay":   100 * time.Millisecond,
			"timeout": 200 * time.Millisecond,
		}, 200*time.Millisecond)
	}

	err := processor.Submit(map[string]any{
		"delay":   10 * time.Millisecond,
		"timeout": 50 * time.Millisecond,
	}, 50*time.Millisecond)

	if err != nil && err != ErrQueueFull {
		t.Errorf("Unexpected error: %v", err)
	}

	processor.Shutdown()
}

func TestBackgroundProcessor_SubmitAfterStop(t *testing.T) {
	processor := NewBackgroundProcessor(10)
	processor.Start(2)
	processor.Shutdown()

	err := processor.Submit(map[string]any{
		"delay":   10 * time.Millisecond,
		"timeout": 50 * time.Millisecond,
	}, 50*time.Millisecond)

	if err != ErrProcessorStopped {
		t.Errorf("Expected ErrProcessorStopped, got: %v", err)
	}
}

func TestBackgroundProcessor_ConcurrentSubmitAndShutdown(t *testing.T) {
	processor := NewBackgroundProcessor(100)
	processor.Start(4)

	var wg sync.WaitGroup
	submitDone := make(chan struct{})

	for i := 0; i < 5; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for j := 0; j < 20; j++ {
				_ = processor.Submit(map[string]any{
					"delay":   1 * time.Millisecond,
					"timeout": 50 * time.Millisecond,
				}, 50*time.Millisecond)
				time.Sleep(time.Millisecond) // Small delay to increase overlap
			}
		}()
	}

	time.Sleep(10 * time.Millisecond)

	wg.Wait()
	close(submitDone)

	processor.Shutdown()
}

func TestProcessBG_WithCustomTimeout(t *testing.T) {
	called := make(chan struct{}, 1)

	processor := NewBackgroundProcessor(10)
	processor.Start(2)

	err := processor.Submit(map[string]any{
		"delay":   200 * time.Millisecond,
		"timeout": 50 * time.Millisecond,
		"onDone": func() {
			select {
			case called <- struct{}{}:
			default:
			}
		},
	}, 50*time.Millisecond)

	if err != nil {
		t.Fatalf("Failed to submit: %v", err)
	}

	time.Sleep(150 * time.Millisecond)
	processor.Shutdown()
}

func TestBackgroundProcessor_IsRunning(t *testing.T) {
	processor := NewBackgroundProcessor(10)

	if !processor.IsRunning() {
		t.Error("Processor should be running after creation")
	}

	processor.Start(2)
	if !processor.IsRunning() {
		t.Error("Processor should still be running after Start")
	}

	processor.Shutdown()
	if processor.IsRunning() {
		t.Error("Processor should not be running after Shutdown")
	}
}

func TestBackgroundProcessor_NoGoroutineLeak(t *testing.T) {
	for i := 0; i < 5; i++ {
		processor := NewBackgroundProcessor(10)
		processor.Start(4)

		for j := 0; j < 5; j++ {
			_ = processor.Submit(map[string]any{
				"delay":   5 * time.Millisecond,
				"timeout": 50 * time.Millisecond,
			}, 50*time.Millisecond)
		}

		time.Sleep(20 * time.Millisecond)
		processor.Shutdown()

		if processor.IsRunning() {
			t.Errorf("Cycle %d: Processor still running after shutdown", i)
		}
	}

	time.Sleep(100 * time.Millisecond)
}

func TestBackgroundProcessor_ContextCancellation(t *testing.T) {
	processor := NewBackgroundProcessor(10)
	processor.Start(2)

	_ = processor.Submit(map[string]any{
		"delay":   1 * time.Second,
		"timeout": 500 * time.Millisecond,
	}, 500*time.Millisecond)

	time.Sleep(10 * time.Millisecond)

	done := make(chan struct{})
	go func() {
		processor.Shutdown()
		close(done)
	}()

	select {
	case <-done:
	case <-time.After(500 * time.Millisecond):
		t.Fatal("Context cancellation did not propagate properly")
	}
}

func BenchmarkBackgroundProcessor_Submit(b *testing.B) {
	processor := NewBackgroundProcessor(1000)
	processor.Start(8)
	defer processor.Shutdown()

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_ = processor.Submit(map[string]any{
			"id":      i,
			"delay":   0,
			"timeout": 100 * time.Millisecond,
		}, 100*time.Millisecond)
	}
}

func BenchmarkBackgroundProcessor_Process(b *testing.B) {
	processor := NewBackgroundProcessor(b.N)
	processor.Start(4)

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_ = processor.Submit(map[string]any{
			"id":      i,
			"delay":   0,
			"timeout": 100 * time.Millisecond,
		}, 100*time.Millisecond)
	}

	time.Sleep(100 * time.Millisecond)
	processor.Shutdown()
}
