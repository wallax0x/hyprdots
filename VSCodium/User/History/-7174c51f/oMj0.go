package main
import ("fmt" 
        "net/http")
func olaMundo(w http.ResponseWriter, r *http.Request) {
	fmt.Fprintf(w, "EAE ESSE SITE ESTA RODANDO EM GO")
}
func main() {
	http.HandleFunc("/", OlaMundo)
	fmt.Println("servidor rodando na porta 8080")
	http.ListenAndServe(":8080", nil)
}