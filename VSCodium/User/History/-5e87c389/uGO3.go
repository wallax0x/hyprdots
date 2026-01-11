package main

import (
	"fmt"
	"html/template"
	"log"
	"net/http"
	"strconv"

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
	protegidas := r.Group("/")
	protegidas.Use(authMiddleware()) // Ativa o segurança aqui
	{
		protegidas.GET("/cadastro", cadastroHandler) // Só empresa logada vê o form
		protegidas.POST("/vagas", criarVagaHandler)  // Só empresa logada posta

		protegidas.GET("/dashboard", dashboardHandler)
		protegidas.POST("/vagas/delete/:id", deletarVagaHandler)
	}

	// ROTA GET: Tela de login do candidato
	r.GET("/candidato/login", func(c *gin.Context) {
		c.HTML(http.StatusOK, "login_candidato.html", gin.H{})
	})
	// ROTA PARA APLICAR (Candidato logado)
	r.POST("/aplicar/:vaga_id", aplicarVagaHandler)
	// ROTA POST: Processar o login
	r.POST("/candidato/login", func(c *gin.Context) {
		email := c.PostForm("email")
		senha := c.PostForm("senha")

		// 1. Buscar Candidato pelo Email
		var candidato models.Candidato
		if err := database.DB.Where("email = ?", email).First(&candidato).Error; err != nil {
			c.HTML(http.StatusBadRequest, "login_candidato.html", gin.H{"error": "Email não encontrado."})
			return
		}

		// 2. Conferir Senha
		if err := bcrypt.CompareHashAndPassword([]byte(candidato.Senha), []byte(senha)); err != nil {
			c.HTML(http.StatusUnauthorized, "login_candidato.html", gin.H{"error": "Senha incorreta."})
			return
		}

		// 3. Criar Cookie "candidato_id" (Diferente do "empresa_id"!)
		c.SetCookie("candidato_id", fmt.Sprintf("%d", candidato.ID), 3600*24, "/", "", false, true)

		// Manda pra Home
		c.Redirect(http.StatusFound, "/")
	})

	// Rota 1: Mostrar a tela de registro
	r.GET("/registro", func(c *gin.Context) {
		c.HTML(http.StatusOK, "registro_empresa.html", gin.H{
			"title": "Crie sua conta - GaranhunsJobs",
		})
	})
	// --- ROTA DO PAINEL DO CANDIDATO ---
	r.GET("/candidato/dashboard", func(c *gin.Context) {
		// 1. Pegar ID do cookie
		candidatoID, err := c.Cookie("candidato_id")
		if err != nil {
			c.Redirect(http.StatusFound, "/candidato/login")
			return
		}

		// 2. Buscar Candidaturas + Dados da Vaga + Dados da Empresa
		var candidaturas []models.Candidatura
		// O Preload carrega os dados das outras tabelas
		database.DB.Preload("Vaga.Empresa").Where("candidato_id = ?", candidatoID).Find(&candidaturas)

		// 3. Renderizar
		c.HTML(http.StatusOK, "dashboard_candidato.html", gin.H{
			"candidaturas": candidaturas,
			"isCandidato":  true,
		})
	})
	// ROTA: Cancelar Candidatura
	r.POST("/candidatura/cancelar/:id", func(c *gin.Context) {
		// 1. Pegar ID da Candidatura (vem da URL)
		candidaturaID := c.Param("id")

		// 2. Pegar ID do Candidato (vem do Cookie - Segurança)
		candidatoCookie, _ := c.Cookie("candidato_id")

		// 3. Buscar e Deletar
		// O Where garante que ninguém cancele a candidatura do vizinho
		var candidatura models.Candidatura
		result := database.DB.Where("id = ? AND candidato_id = ?", candidaturaID, candidatoCookie).Delete(&candidatura)

		if result.Error != nil {
			// Se der erro técnico
			c.Redirect(http.StatusFound, "/candidato/dashboard?msg=erro")
			return
		}

		// 4. Volta pro Dashboard atualizado
		c.Redirect(http.StatusFound, "/candidato/dashboard")
	})

	// ROTA GET: Mostrar formulário do candidato
	r.GET("/candidato/registro", func(c *gin.Context) {
		c.HTML(http.StatusOK, "registro_candidato.html", gin.H{})
	})

	// ROTA POST: Salvar candidato
	r.POST("/candidato/registro", func(c *gin.Context) {
		nome := c.PostForm("nome")
		email := c.PostForm("email")
		cpf := c.PostForm("cpf")
		senha := c.PostForm("senha")
		skills := c.PostForm("skills")

		// 1. Criptografar senha
		hash, err := bcrypt.GenerateFromPassword([]byte(senha), 10)
		if err != nil {
			c.HTML(http.StatusInternalServerError, "registro_candidato.html", gin.H{"error": "Erro no sistema"})
			return
		}

		// 2. Criar objeto Candidato
		novoCandidato := models.Candidato{
			Nome:   nome,
			Email:  email,
			CPF:    cpf,
			Senha:  string(hash),
			Skills: skills,
		}

		// 3. Salvar no Banco
		if result := database.DB.Create(&novoCandidato); result.Error != nil {
			c.HTML(http.StatusBadRequest, "registro_candidato.html", gin.H{
				"error": "Erro ao cadastrar. Email ou CPF já existem?",
			})
			return
		}

		// Sucesso! Por enquanto manda pra Home
		c.Redirect(http.StatusFound, "/")
	})
	// Rota de Logout (Sair)
	r.GET("/logout", func(c *gin.Context) {
		// "Destrói" o cookie definindo tempo negativo (-1)
		c.SetCookie("empresa_id", "", -1, "/", "", false, true)

		// Redireciona para a página inicial
		c.Redirect(http.StatusFound, "/")
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
func authMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		// Tenta ler o cookie
		cookie, err := c.Cookie("empresa_id")

		if err != nil {
			// Se não tiver cookie, chuta pro Login
			c.Redirect(http.StatusFound, "/login")
			c.Abort() // Para tudo, não deixa carregar a página
			return
		}

		// Se tiver cookie, avisa o Gin que o usuário existe
		c.Set("usuario_id", cookie)

		// Pode passar, cidadão!
		c.Next()
	}
}

func homeHandler(c *gin.Context) {
	var vagas []models.Vaga
	database.DB.Preload("Empresa").Order("created_at desc").Find(&vagas)

	// Checa se é Empresa
	_, errEmpresa := c.Cookie("empresa_id")
	isEmpresa := (errEmpresa == nil)

	// Checa se é Candidato
	_, errCandidato := c.Cookie("candidato_id")
	isCandidato := (errCandidato == nil)

	c.HTML(http.StatusOK, "home.html", gin.H{
		"vagas":       vagas,
		"isEmpresa":   isEmpresa,                // Envia status da empresa
		"isCandidato": isCandidato,              // Envia status do candidato
		"isLogado":    isEmpresa || isCandidato, // Se qualquer um tiver logado
	})
}

func cadastroHandler(c *gin.Context) {
	c.HTML(http.StatusOK, "form_vaga.html", gin.H{})
}

func criarVagaHandler(c *gin.Context) {
	usuarioID, _ := c.Get("usuario_id")

	// Converter de String para Uint (o banco pede número)
	empresaIDInt, _ := strconv.Atoi(usuarioID.(string))
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
		EmpresaID:   uint(empresaIDInt),
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

func dashboardHandler(c *gin.Context) {
	// 1. Pegar o ID do usuário (que o Middleware guardou)
	usuarioIDString, _ := c.Get("usuario_id")

	// 2. Buscar APENAS as vagas dessa empresa
	var vagas []models.Vaga
	// O Where filtra: "empresa_id = usuarioIDString"
	database.DB.Where("empresa_id = ?", usuarioIDString).Order("created_at desc").Find(&vagas)

	// 3. Renderizar
	c.HTML(http.StatusOK, "dashboard.html", gin.H{
		"vagas":    vagas,
		"isLogado": true, // Para o menu ficar certo
	})
}
func deletarVagaHandler(c *gin.Context) {
	// 1. Pegar o ID da Vaga que veio na URL
	idVaga := c.Param("id")

	// 2. Pegar o ID da Empresa logada (Segurança!)
	usuarioID, _ := c.Get("usuario_id")

	// 3. Buscar a vaga no banco
	var vaga models.Vaga
	// Verifica se a vaga existe E se pertence a essa empresa
	if err := database.DB.Where("id = ? AND empresa_id = ?", idVaga, usuarioID).First(&vaga).Error; err != nil {
		// Se não achou (ou a vaga não é dela), dá erro
		c.HTML(http.StatusForbidden, "dashboard.html", gin.H{"error": "Operação não permitida."})
		return
	}

	// 4. Deletar (Soft Delete do GORM - ele marca como deletada mas mantém no banco)
	// Se quiser deletar pra sempre, usaria .Unscoped().Delete(&vaga)
	database.DB.Delete(&vaga)

	// 5. Volta pro Dashboard atualizado
	c.Redirect(http.StatusFound, "/dashboard")
}
func aplicarVagaHandler(c *gin.Context) {
	// 1. Verificar se é Candidato (tem o cookie?)
	candidatoID, err := c.Cookie("candidato_id")
	if err != nil {
		// Se não for candidato, manda logar
		c.Redirect(http.StatusFound, "/candidato/login")
		return
	}

	vagaID := c.Param("vaga_id")

	// 2. Verificar se já não se candidatou antes (Duplicidade)
	var existe models.Candidatura
	if err := database.DB.Where("candidato_id = ? AND vaga_id = ?", candidatoID, vagaID).First(&existe).Error; err == nil {
		// Se não deu erro, é porque achou! Já existe.
		// Aqui poderíamos mandar uma mensagem de erro, mas por simplicidade vamos só voltar pra home
		c.Redirect(http.StatusFound, "/")
		return
	}

	// 3. Salvar a Candidatura
	// Converter IDs de String para Uint (Necessário para o GORM)
	cIDInt, _ := strconv.Atoi(candidatoID)
	vIDInt, _ := strconv.Atoi(vagaID)

	novaCandidatura := models.Candidatura{
		CandidatoID: uint(cIDInt),
		VagaID:      uint(vIDInt),
	}

	database.DB.Create(&novaCandidatura)

	// Sucesso!
	c.Redirect(http.StatusFound, "/")
}
