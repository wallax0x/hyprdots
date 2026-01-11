package models

import "gorm.io/gorm"

type Candidato struct {
	gorm.Model
	Nome             string `gorm:"not null"`
	Email            string `gorm:"unique;not null"`
	Senha            string `gorm:"not null"`
	CPF              string `gorm:"unique"`
	Telefone         string
	Bio              string // Um resumo sobre ele
	Skills           string // Ex: "Go, Python, SQL"
	ArquivoCurriculo string
}
