package main

import (
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
)

type GithubResponse struct {
	Name      string `json:"name"`
	Login     string `json:"login"`
	Followers int    `json:"followers"`
	Bio       string `json:"bio"`
}

func executar() {
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
		var usuario GithubResponse
		if err := json.Unmarshal(body, &usuario); err != nil {
			log.Fatal(err)
		}

		// os dados separadamente
		fmt.Printf("Nome: %s\n", usuario.Name)
		fmt.Printf("Usuario: %s\n", usuario.Login)
		fmt.Printf("Seguidores: %d\n", usuario.Followers)
		fmt.Printf("BIOGRAFIA:%s\n", usuario.Bio)

		// Faz a requisição

	}

	// Converte os bytes para string e imprime
	fmt.Printf("resposta do github:\n%s", string(body))
	defer resp.Body.Close()
}
