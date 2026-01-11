package database

import (
	"log"

	"github.com/wallax0x/garan-vagas/models" // <--- IMPORTANTE: Importando as models
	"gorm.io/driver/sqlite"
	"gorm.io/gorm"
)

var DB *gorm.DB

func Connect() {
	var err error
	// Abre a conexão
	DB, err = gorm.Open(sqlite.Open("garanhunsJobs.db"), &gorm.Config{})
	if err != nil {
		log.Fatal("Falha ao conectar ao banco de dados:", err)
	}

	// === AQUI ESTÁ O QUE FALTOU ===
	// Isso cria as tabelas 'empresas', 'candidatos' e 'vagas' automaticamente
	err = DB.AutoMigrate(&models.Empresa{}, &models.Candidato{}, &models.Vaga{})
	if err != nil {
		log.Fatal("Erro ao criar as tabelas no banco:", err)
	}

	log.Println("Conexão e Migração realizadas com sucesso!")
}
