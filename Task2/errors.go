package taskqueue

import "errors"

var (
	ErrProcessorStopped = errors.New("processor is stopped")
	
	ErrQueueFull = errors.New("task queue is full")
)
