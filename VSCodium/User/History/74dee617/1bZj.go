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
	usuarioAlvo := "wallax0x"

	// 1. Verifica argumento
	if len(os.Args) > 1 {
		usuarioAlvo = os.Args[1]
	}

	nomeDoArquivo := usuarioAlvo + ".json"

	// --- MUDANÇA 1: Criamos a variável 'body' vazia aqui fora ---
	var body []byte

	fmt.Printf("🔍 Buscando dados de: %s...\n", usuarioAlvo)

	// --- MUDANÇA 2: Tentamos ler do arquivo primeiro (CACHE) ---
	arquivoLido, errArquivo := os.ReadFile(nomeDoArquivo)

	if errArquivo == nil {
		// CENÁRIO A: O arquivo existe!
		fmt.Println("💾 Opa! Já tenho isso salvo no computador. Lendo arquivo...")
		body = arquivoLido // O corpo recebe o que estava no arquivo

	} else {
		// CENÁRIO B: O arquivo NÃO existe (Deu erro ao ler).
		// Então temos que baixar da internet.
		fmt.Println("🌍 Não tenho esse arquivo. Baixando da internet...")

		url := "https://api.github.com/users/" + usuarioAlvo
		resp, err := http.Get(url)
		if err != nil {
			log.Fatal(err)
		}

		// Verificação de erro 404 (Usuário não existe)
		if resp.StatusCode != 200 {
			log.Fatalf("❌ Erro: Não consegui achar o usuário '%s'. (Status: %d)", usuarioAlvo, resp.StatusCode)
		}

		defer resp.Body.Close()

		// Lemos os dados da internet e colocamos na variável body
		body, err = io.ReadAll(resp.Body)
		if err != nil {
			log.Fatal(err)
		}

		// Já que baixamos agora, vamos aproveitar e salvar para a próxima vez
		err = os.WriteFile(nomeDoArquivo, body, 0644)
		if err != nil {
			log.Fatal("Erro ao salvar arquivo:", err)
		}
		fmt.Printf("✅ Acabei de baixar e salvar em: %s\n", nomeDoArquivo)
	}

	// --- DAQUI PARA BAIXO, NADA MUDA ---
	// O código não sabe se o 'body' veio da internet ou do arquivo,
	// ele só processa o que estiver lá.

	var usuario GithubResponse
	if err := json.Unmarshal(body, &usuario); err != nil {
		log.Fatal(err)
	}

	fmt.Println("--------------------------------")
	fmt.Printf("Nome:       %s\n", usuario.Name)
	fmt.Printf("Usuario:    %s\n", usuario.Login)
	fmt.Printf("Seguidores: %d\n", usuario.Followers)
	fmt.Printf("BIOGRAFIA:  %s\n", usuario.Bio)
	fmt.Println("--------------------------------")
}
