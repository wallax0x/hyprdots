package models

import "gorm.io/gorm"

type Vaga struct {
	gorm.Model
	Titulo      string
	Descricao   string
	Salario     string
	Localizacao string
	Tipo        string // CLT, PJ, Estágio

	// RELACIONAMENTO (Chave Estrangeira)
	// Isso diz: "Essa vaga pertence a esta EmpresaID"
	EmpresaID uint
	Empresa   Empresa `gorm:"constraint:OnUpdate:CASCADE,OnDelete:CASCADE;"`
}
