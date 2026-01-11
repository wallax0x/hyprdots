package main

import (
	"html/template"
	"log"
	"net/http"

	// ... outros imports ...
	// <--- Adicione este
	"github.com/gin-gonic/gin"
	"github.com/wallax0x/garan-vagas/database"
	"github.com/wallax0x/garan-vagas/models"
)

func main() {
	database.Connect()

	database.DB.AutoMigrate(&models.Vaga{})

	seedDatabase()

	r := gin.Default()

	tmpl := template.Must(template.ParseGlob("templates/layouts/*.html"))
	tmpl = template.Must(tmpl.ParseGlob("templates/views/*.html"))
	r.SetHTMLTemplate(tmpl)

	r.Static("/assets", "./assets")

	r.GET("/", homeHandler)
	r.GET("/cadastro", cadastroHandler)
	r.POST("/vagas", criarVagaHandler)

	log.Println("Servidor iniciado em http://0.0.0.0:5000")
	r.Run("0.0.0.0:5000")
}

func seedDatabase() {
	var count int64
	database.DB.Model(&models.Vaga{}).Count(&count)

	if count == 0 {
		// 1. Primeiro cria uma empresa de exemplo
		empresaExemplo := models.Empresa{
			NomeFantasia: "TechGaranhuns",
			CNPJ:         "00.000.000/0001-00",
			Email:        "contato@techgaranhuns.com.br",
			Senha:        "123456", // Num mundo real, isso seria hash
			Cidade:       "Garanhuns",
			Ativa:        true, // Importante: Já nasce aprovada para o teste
		}
		database.DB.Create(&empresaExemplo)

		// 2. Agora cria a vaga usando o ID dessa empresa
		vagaExemplo := models.Vaga{
			Titulo:      "Desenvolvedor Go Pleno",
			Descricao:   "Estamos procurando um dev Go...",
			Salario:     "R$ 6.000 - R$ 9.000",
			Localizacao: "Garanhuns, PE",
			Tipo:        "CLT",
			EmpresaID:   empresaExemplo.ID, // <--- O PULO DO GATO AQUI
		}
		database.DB.Create(&vagaExemplo)

		log.Println("Banco de dados populado com sucesso!")
	}
}

func homeHandler(c *gin.Context) {
	var vagas []models.Vaga
	// "Preload" diz: Aproveita e carrega os dados da tabela Empresa associada
	database.DB.Preload("Empresa").Order("created_at desc").Find(&vagas)

	c.HTML(http.StatusOK, "home.html", gin.H{
		"vagas": vagas,
	})
}

func cadastroHandler(c *gin.Context) {
	c.HTML(http.StatusOK, "form_vaga.html", gin.H{})
}

func criarVagaHandler(c *gin.Context) {
	// Pegamos os dados do form
	titulo := c.PostForm("titulo")
	descricao := c.PostForm("descricao")
	salario := c.PostForm("salario")
	localizacao := c.PostForm("localizacao")
	tipo := c.PostForm("tipo")

	// OBS: Como não temos login ainda, vamos forçar que a vaga
	// pertença à Empresa de ID 1 (que criamos no Seed).
	// Depois, quando tivermos login, vamos pegar o ID da sessão do usuário.
	vaga := models.Vaga{
		Titulo:      titulo,
		Descricao:   descricao,
		Salario:     salario,
		Localizacao: localizacao,
		Tipo:        tipo,
		EmpresaID:   1, // <--- Temporário até fazermos o Login!
	}

	result := database.DB.Create(&vaga)
	if result.Error != nil {
		log.Println("Erro ao criar vaga:", result.Error)
		c.HTML(http.StatusInternalServerError, "form_vaga.html", gin.H{
			"error": "Erro ao criar vaga.",
		})
		return
	}

	c.Redirect(http.StatusFound, "/")
}
