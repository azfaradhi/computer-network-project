## How to Run

```bash
cd src
```
</br>

Terminal 1:
``` bash
python Server.py
```

Terminal2:
``` bash
python Client.py
```


KALO MAU COBA CLIENT KE CLIENT
TERMINAL 1
python Server.py -i localhost -p 1234

TERMINAL 2
python Client.py -cp 4001 -m "Hello from Client 1"

TERMINAL 3
python Client.py -cp 4002 -m "Hello from Client 2"

TERMINAL 4
python Client.py -cp 4003 -m "Hello from Client 3"

COMMAND NYA
Broadcast: broadcast Hello everyone!
Private message: private 4002 Hi Client 2! (contoh dari Client 1 ke Client 2)
