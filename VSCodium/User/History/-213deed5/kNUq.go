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

	defer resp.Body.Close()
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		log.Fatal(err)
	}
	var usuario GithubResponse
	if err := json.Unmarshal(body, &usuario); err != nil {
		log.Fatal(err)
	}

	fmt.Println("--------------------------------")
	fmt.Printf("Nome: %s\n", usuario.Name)
	fmt.Printf("Usuario: %s\n", usuario.Login)
	fmt.Printf("Seguidores: %d\n", usuario.Followers)
	fmt.Printf("BIOGRAFIA:%s\n", usuario.Bio)
	fmt.Println("--------------------------------")

}
