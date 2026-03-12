package main

import (
	"encoding/json"
	"fmt"
	"os"
)

type Input struct {
	Val int `json:"val"`
}

type Output struct {
	Result int `json:"result"`
}

func main() {
	var input Input

	decoder := json.NewDecoder(os.Stdin)
	if err := decoder.Decode(&input); err != nil {
		fmt.Fprintf(os.Stderr, "Error decoding input: %v\n", err)
		os.Exit(1)
	}

	output := Output{
		Result: input.Val * 2,
	}

	encoder := json.NewEncoder(os.Stdout)
	if err := encoder.Encode(output); err != nil {
		fmt.Fprintf(os.Stderr, "Error encoding output: %v\n", err)
		os.Exit(1)
	}
}
