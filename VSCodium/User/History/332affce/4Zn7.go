package main

import (
	"encoding/json"
	"fmt"
	"net/http"
	"time"
)

// molde do perfil
type Perfil struct {
	Usuario string `json:"usuario"`
	Cargo   string `json:"cargo"`
	Nivel   int    `json:"nivel"`
}

func iniCio(w http.ResponseWriter, r *http.Request) {
	fmt.Fprintf(w, "<h1>Bem-vindo ao meu servidor</h1><p> ESSE SITE ESTA RODANDO EM GO NO GENTOO LINUX</P>")
}
func exenome(w http.ResponseWriter, r *http.Request) {
	// define que a resposta e do tipo json
	w.Header().Set("Content-Type", "aplication/json")
	//cria os dados usando o molde
	meuPerfil := Perfil{Usuario: "Mauricio", Cargo: "Admin", Nivel: 100}
	//envia codificado
	json.NewEncoder(w).Encode(meuPerfil)
}
func info(w http.ResponseWriter, r *http.Request) {
	agora := time.Now().Format("15:04:05")
	fmt.Fprintf(w, "Hora do servidor: %s\nStatus: Online", agora)
}
func main() {
	http.HandleFunc("/", iniCio)
	http.HandleFunc("/info", info)
	http.HandleFunc("/nome", exenome)
	fmt.Println("servidor rodando na porta 8080")

	err := http.ListenAndServe(":8080", nil)
	if err != nil {
		fmt.Println("Erro", err)
	}
}
