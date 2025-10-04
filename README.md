# projeto1-comp-conc-par-dist

Este repositório contém a implementação de um sistema distribuído simples, no modelo cliente-servidor, que simula um banco de dados chave-valor em memória. 

O projeto serve como uma demonstração prática e fundamental de como sistemas de alto desempenho são construídos, sendo aplicável a casos de uso reais como serviços de cache, armazenamento de sessões de usuário e filas de mensagens. Desenvolvido em Python 3.11+ utilizando apenas bibliotecas padrão, o foco principal é demonstrar de forma clara e isolada os conceitos essenciais de concorrência, paralelismo e sincronização. 

### 📂 Estrutura do Repositório 

- server.py: O coração do sistema. Este script implementa o servidor central TCP, responsável por gerenciar o ciclo de vida da aplicação, escutar por novas conexões, gerenciar o armazenamento de dados em memória e delegar tarefas computacionalmente intensivas para um pool de processos worker. 

- client.py: A interface de usuário para o serviço. Este cliente de terminal interativo permite que uma pessoa se conecte ao servidor e execute manualmente as operações de PUT, GET, DELETE e DUMP, facilitando testes e demonstrações diretas. 


- tester.py: A ferramenta de validação e estresse. Este script automatizado é crucial para provar a robustez do servidor, simulando uma carga de múltiplos clientes concorrentes que executam operações aleatórias. Ao final, ele valida a consistência dos dados, garantindo que os mecanismos de sincronização funcionam corretamente sob pressão. 


### 💡 Conceitos Demonstrados 


- Arquitetura Cliente-Servidor: A comunicação é estabelecida sobre o protocolo TCP, garantindo uma entrega de dados confiável e ordenada. O servidor abre um socket em uma porta conhecida e aguarda conexões. Quando um cliente se conecta, um canal de comunicação bidirecional e persistente é estabelecido. 

- Concorrência (threading): Para alcançar alta responsividade, o servidor é capaz de atender a vários clientes simultaneamente. Cada nova conexão é gerenciada em sua própria Thread, permitindo que o servidor processe múltiplas requisições de forma intercalada, garantindo que um cliente executando uma operação lenta não bloqueie todos os outros. 


- Paralelismo (multiprocessing): Embora o threading ofereça concorrência, o Global Interpreter Lock (GIL) do Python impede que múltiplas threads executem código Python em paralelo. Para contornar isso e simular tarefas verdadeiramente pesadas, o servidor utiliza um Pool de Processos. Tarefas como PUT são enviadas para uma multiprocessing.Queue, e os processos trabalhadores as consomem, alcançando paralelismo real. 

- Sincronização (threading.Lock): O dicionário que armazena os dados é um recurso compartilhado (região crítica). Para evitar condições de corrida, todas as operações de leitura e escrita no dicionário são protegidas por um threading.Lock, que garante que apenas uma thread possa acessar os dados por vez, mantendo a integridade do estado. 

- Comunicação entre Processos (multiprocessing.Queue): Como threads e processos operam em espaços de memória distintos, a multiprocessing.Queue é usada para fornecer uma estrutura de dados segura para que as threads de cliente enviem tarefas aos processos trabalhadores de forma simples e confiável. 

### 🚀 Como Executar 

Você precisará do Python 3.11 ou superior. Nenhuma biblioteca externa é necessária. 

1. **Iniciar o Servidor** 

Abra um terminal e execute: 
```
Bash

python server.py
```
O servidor permanecerá em execução, exibindo logs sobre seu status e as conexões de novos clientes. 

2. *(Opcional) Usar o Cliente Interativo* 

Abra outro terminal para interagir com o servidor: 

```
Bash

python client.py
```
Você pode agora digitar comandos: 

- POST minha_chave meu_valor

- PUT minha_chave meu_valor 

- GET minha_chave 

- DELETE minha_chave 

- DUMP 

- exit (para sair) 

3. **Executar o Teste de Concorrência** 

Para uma verificação rigorosa, abra um terceiro terminal e execute o script de teste: 

```
Bash

python tester.py
```

O script irá: 

- Simular múltiplos clientes executando operações concorrentes. 

- Calcular e exibir o throughput (operações por segundo). 

- Ao final, comparar o estado final do servidor com um estado local esperado para validar a consistência. 

- Exibir uma mensagem de SUCESSO se os estados forem idênticos, ou FALHA caso contrário. 

### 📈 Sugestões de Melhorias e Métricas de Avaliação 

#### **Métricas de Avaliação:**

- Latência: Medir o tempo de ida e volta (round-trip time) para cada operação no lado do cliente. 

- Throughput: O número de operações por segundo que o servidor consegue processar. O tester.py já implementa uma medição básica. 

- Corretude: A capacidade do sistema de manter a consistência dos dados sob carga. Validada pelo tester.py. 

- Uso de CPU/Memória: Monitorar os recursos consumidos pelo servidor e pelos workers para entender a eficiência do sistema.

#### **Possíveis Melhorias**


- Read-Write Lock (RWLock): Em cenários com mais leituras (GET) do que escritas, um RWLock permitiria múltiplas leituras simultâneas, otimizando o desempenho. 


- Persistência Real: Implementar a escrita dos dados em um arquivo (JSON, CSV, SQLite) para garantir durabilidade, em vez de simular com time.sleep(). 


- Protocolo Robusto: Utilizar um formato de serialização como JSON para as mensagens, a fim de tornar o protocolo menos frágil e permitir o retorno de códigos de erro claros. 


- Graceful Shutdown: Implementar um mecanismo para que o servidor notifique os clientes sobre um desligamento iminente, permitindo que eles se desconectem de forma limpa. 


- Replicação: Para alta disponibilidade, estender a tarefa do worker para replicar as operações de escrita em outros servidores-réplica, tornando o sistema tolerante a falhas. 
