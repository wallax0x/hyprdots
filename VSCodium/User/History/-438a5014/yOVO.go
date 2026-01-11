package models

import "gorm.io/gorm"

type Empresa struct {
	gorm.Model
	NomeFantasia string `gorm:"not null"`
	CNPJ         string `gorm:"unique;not null"` // Único para evitar duplicidade
	Email        string `gorm:"unique;not null"`
	Senha        string `gorm:"not null"` // Vamos guardar o Hash (criptografada)
	Telefone     string
	Cidade       string
	Sobre        string

	// AQUI ESTÁ A MÁGICA DA SEGURANÇA:
	Ativa bool `gorm:"default:false"` // Nasce bloqueada. Você (Admin) precisa ativar.
}
