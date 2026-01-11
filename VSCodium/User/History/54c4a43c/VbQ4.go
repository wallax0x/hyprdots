package database

import (
	"log"

	"github.com/wallax0x/garan-vagas/models"
	"gorm.io/driver/sqlite"
	"gorm.io/gorm"
)

var DB *gorm.DB

func Conectar() {
	var err error
	DB, err = gorm.Open(sqlite.Open("vagas.db"), &gorm.Config{})

	if err != nil {
		log.Panic("Falha ao conectar no banco de dados!")
	}

	DB.AutoMigrate(&models.Vaga{})
}
