package main

import (
	"fmt"
	"io"
	"log"
	"net/http"
)

func executar() {
	// Faz a requisição
	resp, err := http.Get("https://api.github.com/users/wallax0x")
	if err != nil {
		log.Fatal(err)
	}
	// IMPORTANTE: Fecha o corpo da resposta quando a função terminar para não vazar memória
	defer resp.Body.Close()

	// Lê o conteúdo do corpo (body) da resposta
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		log.Fatal(err)
	}

	// Converte os bytes para string e imprime
	fmt.Printf("resposta do github:\n%s", string(body))
	defer resp.Body.Close()
}
