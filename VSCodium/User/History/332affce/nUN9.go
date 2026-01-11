package main

import (
	"fmt"
	"net/http"
	"time"
)

func iniCio(w http.ResponseWriter, r *http.Request) {
	fmt.Fprintf(w, "<h3>wallax</h3><p> ESSE SITE ESTA RODANDO EM GO NO GENTOO LINUX</P>")
}
func info(w http.ResponseWriter, r *http.Request) {
	agora := time.Now().Format("15:04:05")
	fmt.Fprintf(w, "Hora do servidor: %s\nStatus: Online", agora)
}
func main() {
	http.HandleFunc("/", iniCio)
	http.HandleFunc("/info", info)
	fmt.Println("servidor rodando na porta 8080")

	err := http.ListenAndServe(":8080", nil)
	if err != nil {
		fmt.Println("Erro", err)
	}
}
