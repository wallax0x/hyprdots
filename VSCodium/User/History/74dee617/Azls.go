package main

import (
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
)

type GithubResponse struct {
	Name      string `json:"name"`
	Login     string `json:"login"`
	Followers int    `json:"followers"`
	Bio       string `json:"bio"`
}

func executar() {
	usuarioAlvo := "wallax0x" // Valor padrão

	// A chave abre aqui...
	if len(os.Args) > 1 {
		usuarioAlvo = os.Args[1] // ...o comando perigoso fica aqui dentro...
	}

	fmt.Printf("🔍 Buscando dados de: %s...\n", usuarioAlvo)

	url := "https://api.github.com/users/" + usuarioAlvo
	resp, err := http.Get(url)
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
	if resp.StatusCode != 200 {
		log.Fatalf("❌ Erro: Não consegui achar o usuário '%s'. (Status: %d)", usuarioAlvo, resp.StatusCode)
	}

	fmt.Println("--------------------------------")
	fmt.Printf("Nome: %s\n", usuario.Name)
	fmt.Printf("Usuario: %s\n", usuario.Login)
	fmt.Printf("Seguidores: %d\n", usuario.Followers)
	fmt.Printf("BIOGRAFIA:%s\n", usuario.Bio)
	fmt.Println("--------------------------------")

	//salvar no json
	nomeDoArquivo := usuarioAlvo + ".json"
	if err != nil {
		log.Fatal("Erro ao salvar arquivo:", err)
	}
	fmt.Printf("\n✅ Ficha salva com sucesso em: %s\n", nomeDoArquivo)

}
