# ChatTCP — IF2230 Tugas Besar Jaringan Komputer

![Teteh Frieren](https://media3.giphy.com/media/v1.Y2lkPTc5MGI3NjExMWJsZm1qc241dHVheThrbTd0M3p5YWR1YmlxMWkyNmtzZnVnY2xoaCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/dKBES1ypGwZdyFQBQ7/giphy.gif)

**ChatTCP** adalah implementasi custom TCP di atas protokol UDP menggunakan Python socket, dengan fitur-fitur TCP seperti:
- Three-way handshake
- Arbitrary segmentation (≤ 64 byte payload)
- Sliding window (flow control)
- Error detection (checksum)
- FIN-ACK termination
  
Implementasi tersebut digunakan dalam aplikasi chat room sederhana berbasis terminal dan GUI.

Program ini dibuat untuk memenuhi Tugas Besar IF2230 - Jaringan Komputer 2025.

## ⚙️ Setup & Instalasi

**Langkah pertama:** install [uv](https://docs.astral.sh/uv/getting-started/installation/) (pengganti pip + venv).

```bash
uv init chattcp
uv python install 3.13
uv python pin 3.13
```  

## 🚀 Menjalankan Program
Pertama-tama, jalankan server dengan menggunakan command berikut di terminal. Catatan: -i untuk set ip server dan -p untuk set port server.
```bash
uv run src/Server.py -i 127.0.0.1 -p 1234
```
Berikutnya, terdapat dua metode untuk menjalankan clients, yaitu melalui CLI dan GUI.
### CLI
Untuk masing-masing client, jalankan command berikut di terminal yang berbeda. Catatan: -si untuk set ip server yang digunakan, -sp untuk set port server yang digunakan, dan -un untuk menentukan username dari client.
```bash
uv run src/Client.py -si 127.0.0.1 -sp 1234 -un Client1
```
### GUI
Untuk masing-masing client, jalankan command berikut di terminal yang berbeda. Catatan: -si untuk set ip server yang digunakan, -sp untuk set port server yang digunakan, dan -un untuk menentukan username dari client.
```bash
uv run src/main.py -si 127.0.0.1 -sp 1234 -un Client1
```

## 📝 Pembagian Tugas
| NIM       | Nama                   | Tugas                                     |
|-----------|------------------------|-----------------------------------------------------|
| 13523079  | Nayla Zahira           | Flow Control, Aplikasi Chat Room                    |
| 13523092  | Muhammad Izzat Jundy   | TCP Segments, Aplikasi Chat Room                   |
| 13523095  | Rafif Farras           | Flow Control, Aplikasi Chat Room                    |
| 13523101  | Barru Adi Utomo        | Three-Way Handshake, Error Detection, Aplikasi Chat Room |
| 13523115  | Azfa Radhiyya Hakim    | Aplikasi Chat Room, GUI                             |

## 📖 Referensi
- ChatGPT
- [GitHub sebuah kelompok IF '21](https://github.com/Sister20/tugas-besar-if3130-jaringan-komputer-gununge)
