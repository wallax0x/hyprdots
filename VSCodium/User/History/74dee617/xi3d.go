package main

import (
	"encoding/json"
	"fmt"
	"io"
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
	var usuarioAlvo string

	fmt.Println("🤖 BOT INICIADO! (Digite 'sair' para fechar)")

	// --- LOOP INFINITO (O código fica preso aqui dentro) ---
	for {
		fmt.Print("\n👉 Digite o nome do usuário: ")

		// 1. O programa PAUSA e espera você digitar
		fmt.Scanln(&usuarioAlvo)

		// 2. Se digitar "sair", o programa fecha
		if usuarioAlvo == "sair" {
			fmt.Println("👋 Encerrando...")
			break
		}

		// Se der enter sem digitar nada, volta pro começo
		if usuarioAlvo == "" {
			continue
		}

		// --- LÓGICA DE CACHE (IGUAL ANTES) ---
		nomeDoArquivo := usuarioAlvo + ".json"
		var body []byte

		// Tenta ler do arquivo
		arquivoLido, errArquivo := os.ReadFile(nomeDoArquivo)

		if errArquivo == nil {
			fmt.Println("💾 Achei no computador (Cache)!")
			body = arquivoLido
		} else {
			fmt.Println("🌍 Baixando da internet...")
			url := "https://api.github.com/users/" + usuarioAlvo
			resp, err := http.Get(url)
			if err != nil {
				fmt.Println("❌ Erro de conexão:", err)
				continue
			}

			if resp.StatusCode != 200 {
				fmt.Printf("❌ Usuário '%s' não existe (404).\n", usuarioAlvo)
				resp.Body.Close() // Fecha conexão
				continue
			}

			body, _ = io.ReadAll(resp.Body)
			resp.Body.Close() // Importante fechar sempre

			// Salva o arquivo
			os.WriteFile(nomeDoArquivo, body, 0644)
		}

		// --- MOSTRAR DADOS ---
		var usuario GithubResponse
		if err := json.Unmarshal(body, &usuario); err != nil {
			fmt.Println("❌ Erro ao ler JSON:", err)
			continue
		}

		fmt.Println("--------------------------------")
		fmt.Printf("Nome:       %s\n", usuario.Name)
		fmt.Printf("Seguidores: %d\n", usuario.Followers)
		fmt.Println("--------------------------------")

	} // Fim do Loop
}
