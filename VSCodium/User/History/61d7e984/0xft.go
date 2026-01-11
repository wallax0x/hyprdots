package models

import "gorm.io/gorm"

type Vaga struct {
	gorm.Model
	Titulo      string
	Descricao   string
	Salario     string
	Empresa     string
	Localizacao string
	Tipo        string
}
