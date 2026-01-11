package models

import "gorm.io/gorm"

type Candidatura struct {
	gorm.Model
	CandidatoID uint
	VagaID      uint

	// Relacionamentos (para facilitar buscas futuras)
	Candidato Candidato
	Vaga      Vaga
}
