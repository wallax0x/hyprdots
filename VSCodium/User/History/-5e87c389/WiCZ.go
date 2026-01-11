package main

import (
	"fmt"
	"html/template"
	"log"
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/wallax0x/garan-vagas/database"
	"github.com/wallax0x/garan-vagas/models"
	"golang.org/x/crypto/bcrypt"
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
	// Rota 1: Mostrar a tela de registro
	r.GET("/registro", func(c *gin.Context) {
		c.HTML(http.StatusOK, "registro_empresa.html", gin.H{
			"title": "Crie sua conta - GaranhunsJobs",
		})
	})

	// Rota GET: Mostrar tela de login
	r.GET("/login", func(c *gin.Context) {
		c.HTML(http.StatusOK, "login.html", gin.H{})
	})

	// Rota POST: Verificar senha e logar
	r.POST("/login", func(c *gin.Context) {
		email := c.PostForm("email")
		senha := c.PostForm("senha")

		// 1. Buscar a empresa pelo Email
		var empresa models.Empresa
		// O .First tenta achar o primeiro registro com esse email
		if err := database.DB.Where("email = ?", email).First(&empresa).Error; err != nil {
			c.HTML(http.StatusBadRequest, "login.html", gin.H{"error": "Email não cadastrado ou incorreto."})
			return
		}

		// 2. Verificar se a senha bate com o Hash (Bcrypt)
		err := bcrypt.CompareHashAndPassword([]byte(empresa.Senha), []byte(senha))
		if err != nil {
			c.HTML(http.StatusUnauthorized, "login.html", gin.H{"error": "Senha incorreta!"})
			return
		}

		// 3. Login Sucesso: Criar um COOKIE
		// Isso é o que mantém o usuário logado.
		// setCookie(nome, valor, tempo_segundos, path, domain, secure, httpOnly)
		// Convertendo o ID (uint) para String usando fmt.Sprintf
		c.SetCookie("empresa_id", fmt.Sprintf("%d", empresa.ID), 3600*24, "/", "", false, true)

		// Manda para a home (Futuramente mandaremos para o Painel da Empresa)
		c.Redirect(http.StatusFound, "/")
	})

	// Rota 2: Processar o cadastro
	r.POST("/registro", func(c *gin.Context) {
		nome := c.PostForm("nome")
		cnpj := c.PostForm("cnpj")
		email := c.PostForm("email")
		senha := c.PostForm("senha")
		cidade := c.PostForm("cidade")

		// 1. Criptografar a Senha (Hash)
		// O custo 14 é bem seguro, mas pode ser lento. 10 é padrão.
		hash, err := bcrypt.GenerateFromPassword([]byte(senha), 10)
		if err != nil {
			c.HTML(http.StatusInternalServerError, "registro_empresa.html", gin.H{"error": "Erro ao criptografar senha"})
			return
		}

		// 2. Criar o Objeto Empresa
		novaEmpresa := models.Empresa{
			NomeFantasia: nome,
			CNPJ:         cnpj,
			Email:        email,
			Senha:        string(hash), // Salva o HASH, não a senha real!
			Cidade:       cidade,
			Ativa:        true, // Vamos deixar true pra facilitar o teste agora
		}

		// 3. Tentar Salvar no Banco
		result := database.DB.Create(&novaEmpresa)
		if result.Error != nil {
			// Se der erro (ex: email duplicado), avisa o usuário
			c.HTML(http.StatusBadRequest, "registro_empresa.html", gin.H{
				"error": "Erro ao criar conta. Email ou CNPJ já cadastrados?",
			})
			return
		}

		// Se deu certo, manda pra Home (ou pro Login futuramente)
		c.Redirect(http.StatusFound, "/")
	})

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
