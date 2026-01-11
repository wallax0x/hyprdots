package main

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
)

type GithubResponse struct {
	Login           string `json:"login"`
	ID              int    `json:"id"`
	NodeID          string `json:"node_id"`
	AvatarURL       string `json:"avatar_url"`
	HTMLURL         string `json:"html_url"`
	Type            string `json:"type"`
	Name            string `json:"name"`
	Company         string `json:"company"`
	Blog            string `json:"blog"`
	Location        string `json:"location"`
	Email           string `json:"email"` //vazio
	Hireable        bool   `json:"hireable"`
	Bio             string `json:"bio"`
	PublicRepos     int    `json:"public_repos"`
	PublicGists     int    `json:"public_gists"`
	Followers       int    `json:"followers"`
	Following       int    `json:"following"`
	CreatedAt       string `json:"created_at"`
	UpdatedAt       string `json:"updated_at"`
	TwitterUsername string `json:"twitter_username"`
}

func executar() {
	var usuarioAlvo string

	fmt.Println("🤖 BOT GITHUB V2.0 - DADOS COMPLETOS")
	fmt.Println("   (Digite 'sair' para fechar)")

	for {
		fmt.Print("\n👉 Digite o nome do usuário: ")
		fmt.Scanln(&usuarioAlvo)

		if usuarioAlvo == "sair" {
			fmt.Println("👋 Encerrando...")
			break
		}
		if usuarioAlvo == "" {
			continue
		}

		// LOGICA CACHE
		nomeDoArquivo := usuarioAlvo + ".json"
		var body []byte

		arquivoLido, errArquivo := os.ReadFile(nomeDoArquivo)

		if errArquivo == nil {
			fmt.Println("💾 [CACHE] Lendo do arquivo salvo...")
			body = arquivoLido
		} else {
			fmt.Println("🌍 [WEB] Baixando do GitHub...")
			url := "https://api.github.com/users/" + usuarioAlvo
			resp, err := http.Get(url)
			if err != nil {
				fmt.Println("❌ Erro de conexão:", err)
				continue
			}

			if resp.StatusCode != 200 {
				fmt.Printf("❌ Usuário '%s' não existe (404).\n", usuarioAlvo)
				resp.Body.Close()
				continue
			}

			body, _ = io.ReadAll(resp.Body)
			resp.Body.Close()
			os.WriteFile(nomeDoArquivo, body, 0644)
		}

		// --- PROCESSAR DADOS ---
		var u GithubResponse
		if err := json.Unmarshal(body, &u); err != nil {
			fmt.Println("❌ Erro ao ler JSON:", err)
			continue
		}

		// --- IMPRIMIR O RELATÓRIO COMPLETO ---
		fmt.Println("============================================")
		fmt.Printf("👤  NOME:        %s\n", u.Name)
		fmt.Printf("🔑  LOGIN:       %s (ID: %d)\n", u.Login, u.ID)
		fmt.Printf("📝  BIO:         %s\n", u.Bio)
		fmt.Println("--------------------------------------------")
		fmt.Printf("🏢  EMPRESA:     %s\n", u.Company)
		fmt.Printf("📍  LOCAL:       %s\n", u.Location)
		fmt.Printf("🔗  SITE/BLOG:   %s\n", u.Blog)
		fmt.Printf("🐦  TWITTER:     %s\n", u.TwitterUsername)
		fmt.Println("--------------------------------------------")
		fmt.Printf("📦  REPOS PÚBL.: %d\n", u.PublicRepos)
		fmt.Printf("📄  GISTS:       %d\n", u.PublicGists)
		fmt.Printf("👥  SEGUIDORES:  %d\n", u.Followers)
		fmt.Printf("👣  SEGUINDO:    %d\n", u.Following)
		if u.Followers > 100 {
			fmt.Println("UAU ESSE USUARIO E FAMOSO")
		} else {
			fmt.Println("POUCOS SEGUIDORES ESSE USUARIO AINDA ESTA CRESCENDO")

		}
		fmt.Println("--------------------------------------------")
		fmt.Printf("📅  CRIADO EM:   %s\n", u.CreatedAt)
		fmt.Printf("🔄  ATUALIZADO:  %s\n", u.UpdatedAt)
		fmt.Printf("🔗  PERFIL URL:  %s\n", u.HTMLURL)
		fmt.Printf("🖼️   AVATAR URL:  %s\n", u.AvatarURL)

		// Imprime true/false se está disponível para contratação
		if u.Hireable {
			fmt.Println("💼  STATUS:      Disponível para contratação! ✅")
		} else {
			fmt.Println("💼  STATUS:      Não disponível ❌")
		}
		fmt.Println("============================================")
	}
}
