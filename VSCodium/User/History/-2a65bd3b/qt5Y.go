package main

import (
	"net/http"

	"github.com/gin-gonic/gin"
)

func main() {
	// Cria uma instância padrão do Gin (com logs e recovery)
	r := gin.Default()
	r.Static("/assets", "./assets")
	// Isso diz: Dentro de templates > Pegue qualquer pasta (*) > Pegue qualquer arquivo (*)
	r.LoadHTMLGlob("templates/*/*")

	// Carrega os templates HTML (quando criarmos)
	// r.LoadHTMLGlob("templates/**/*")

	// Rota de teste (Página Inicial)
	r.GET("/", func(c *gin.Context) {
		// Ao invés de JSON, agora renderizamos o template "home.html"
		c.HTML(http.StatusOK, "home.html", gin.H{
			"title": "GaranhunsJobs - Vagas na Cidade das Flores",
		})
	})

	//======= ROTAS ========

	// Rota para verificar funcionamento
	r.GET("/ping", func(c *gin.Context) {
		c.JSON(200, gin.H{
			"message": "pong",
		})
	})

	// Rota 1: Mostrar o formulário de cadastro
	r.GET("/cadastro", func(c *gin.Context) {
		c.HTML(http.StatusOK, "form_vaga.html", gin.H{
			"title": "Nova Vaga - GaranhunsJobs",
		})
	})

	// Rota 2: Receber os dados do formulário e SALVAR no banco
	r.POST("/vagas", func(c *gin.Context) {
		// Pega os dados que vieram do HTML
		novaVaga := models.Vaga{
			Titulo:      c.PostForm("titulo"),
			Empresa:     c.PostForm("empresa"),
			Salario:     c.PostForm("salario"),
			Localizacao: c.PostForm("localizacao"),
			Tipo:        c.PostForm("tipo"),
			Descricao:   c.PostForm("descricao"),
		}

		// Manda o GORM salvar no SQLite
		database.DB.Create(&novaVaga)

		// Redireciona o usuário de volta para a Home
		c.Redirect(http.StatusFound, "/")
	})

	//===== FIM DAS ROTAS

	// Roda o servidor na porta 8080
	r.Run(":8080")
}
