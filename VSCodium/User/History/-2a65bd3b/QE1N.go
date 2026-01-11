package main

import (
	"net/http"

	"github.com/gin-gonic/gin"
)

func main() {
	// Cria uma instância padrão do Gin (com logs e recovery)
	r := gin.Default()
	r.Static("/assets", "./assets")

	// Carrega os templates HTML (quando criarmos)
	// r.LoadHTMLGlob("templates/**/*")

	// Rota de teste (Página Inicial)
	r.GET("/", func(c *gin.Context) {
		// Ao invés de JSON, agora renderizamos o template "home.html"
		c.HTML(http.StatusOK, "home.html", gin.H{
			"title": "GaranhunsJobs - Vagas na Cidade das Flores",
		})
	})

	// Rota para verificar funcionamento
	r.GET("/ping", func(c *gin.Context) {
		c.JSON(200, gin.H{
			"message": "pong",
		})
	})

	// Roda o servidor na porta 8080
	r.Run(":8080")
}
