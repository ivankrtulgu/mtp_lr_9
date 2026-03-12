package taskqueue

import (
	"context"
	"sync"
	"time"
)

type Task struct {
	Data    map[string]any
	Timeout time.Duration
}

type BackgroundProcessor struct {
	taskChan    chan Task
	wg          sync.WaitGroup
	ctx         context.Context
	cancel      context.CancelFunc
	mu          sync.RWMutex
	running     bool
	shutdownOnce sync.Once
}

func NewBackgroundProcessor(queueSize int) *BackgroundProcessor {
	ctx, cancel := context.WithCancel(context.Background())
	return &BackgroundProcessor{
		taskChan: make(chan Task, queueSize),
		ctx:      ctx,
		cancel:   cancel,
		running:  true,
	}
}

func (bp *BackgroundProcessor) Start(workers int) {
	bp.mu.Lock()
	defer bp.mu.Unlock()

	if !bp.running {
		return
	}

	for i := 0; i < workers; i++ {
		bp.wg.Add(1)
		go bp.worker(i)
	}
}

func (bp *BackgroundProcessor) worker(id int) {
	defer bp.wg.Done()

	for {
		select {
		case <-bp.ctx.Done():
			return
		case task, ok := <-bp.taskChan:
			if !ok {
				return
			}
			bp.processTask(task)
		}
	}
}

func (bp *BackgroundProcessor) processTask(task Task) {
	ctx, cancel := context.WithTimeout(bp.ctx, task.Timeout)
	defer cancel()

	done := make(chan struct{})
	go func() {
		defer close(done)
		bp.executeTask(task.Data)
	}()

	select {
	case <-done:
	case <-ctx.Done():
	}
}

func (bp *BackgroundProcessor) executeTask(data map[string]any) {
	if delay, ok := data["delay"]; ok {
		if d, ok := delay.(time.Duration); ok {
			time.Sleep(d)
		}
	}
}

func (bp *BackgroundProcessor) Submit(data map[string]any, timeout time.Duration) error {
	bp.mu.RLock()
	running := bp.running
	bp.mu.RUnlock()

	if !running {
		return ErrProcessorStopped
	}

	select {
	case bp.taskChan <- Task{Data: data, Timeout: timeout}:
		return nil
	default:
		return ErrQueueFull
	}
}

func ProcessBG(data map[string]any) {
	processor := NewBackgroundProcessor(100)
	processor.Start(4)

	timeout := 5 * time.Second
	if t, ok := data["timeout"]; ok {
		if td, ok := t.(time.Duration); ok {
			timeout = td
		}
	}

	_ = processor.Submit(data, timeout)
}

func (bp *BackgroundProcessor) Shutdown() {
	bp.mu.Lock()
	bp.running = false
	bp.mu.Unlock()

	bp.cancel()
	close(bp.taskChan)
	bp.wg.Wait()
}

func (bp *BackgroundProcessor) IsRunning() bool {
	bp.mu.RLock()
	defer bp.mu.RUnlock()
	return bp.running
}

func (bp *BackgroundProcessor) QueueLength() int {
	return len(bp.taskChan)
}
