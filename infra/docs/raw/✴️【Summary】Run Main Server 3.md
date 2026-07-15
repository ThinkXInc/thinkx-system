# ✴️【Summary】Run Main Server 3

_created: 20240413T235552Z / updated: 20250425T115022Z_

Logs

gateway-server

```
sudo journalctl -fu gateway-server.service --output cat
```

unix_socket_server

```
sudo journalctl -fu unix_socket_server.service --output cat
```

llm_server

```
sudo journalctl -fu llm_server.service --output cat
```

vectordb_server

```
sudo journalctl -fu vectordb_server.service --output cat
```

workers core (transcribe, process_transcript, handle_llm_tasks, respond, store_chatdata)

```
cd /src/quantz/processing-server
cd tasks_server/service
. ./logs_core.sh
```

workers action (handle_llm_subtask_outputs, select_action)

```
cd /src/quantz/processing-server
cd tasks_server/service
. ./logs_action.sh
```

workers general llm (handle_llm_general_task_outputs_worker, llm_general_task_worker)

```
cd /src/quantz/processing-server
cd tasks_server/service
. ./logs_general.sh
```

* core for each 

transcribe

```
sudo journalctl -fu transcribe.service --output cat -n 1000
```

select_action

```
sudo journalctl -fu select_action.service --output cat
```

handle_select_action

```
sudo journalctl -fu handle_select_action.service --output cat -n 1000
```

handle_chat

```
sudo journalctl -fu handle_chat.service --output cat
```

respond

```
sudo journalctl -fu respond.service --output cat -n 1000
```

store_chatdata

```
sudo journalctl -fu store_chatdata.service --output cat -n 1000
```

---

context_search

```
sudo journalctl -fu context_search.service --output cat -n 1000
```

*core all

workers core all (transcribe, select_action, handle_llm_subtask_outputs, process_transcript, handle_llm_tasks, respond, store_chatdata)

```
cd /src/quantz/processing-server
cd tasks_server/service
. ./logs_core_all.sh
```

Restart

gateway-server

```
cd /src/quantz/gateway-server/service
. ./restart.sh gateway-server
```

unix socket server

```
sudo systemctl restart unix_socket_server.service
```

llm_server

```
sudo systemctl restart llm_server
```

*run local dbs

```
cd /src/quantz/processing-server
docker-compose up -d
```

vector db server

```
sudo systemctl restart vectordb_server.service
```

workers all

```
cd /src/quantz/processing-server
cd tasks_server/service
. ./restart.sh all
```

workers core (transcribe, process_transcript, handle_llm_tasks, respond, store_chatdata)

```
cd /src/quantz/processing-server
cd tasks_server/service
. ./restart.sh core # restart all core services
```

workers general (

```
cd /src/quantz/processing-server
cd tasks_server/service
. ./restart.sh general
```

*workers each

```
cd /src/quantz/processing-server
cd tasks_server/service
. ./restart.sh transcribe
```

```
cd /src/quantz/processing-server
cd tasks_server/service
. ./restart.sh select_action
```

```
cd /src/quantz/processing-server
cd tasks_server/service
. ./restart.sh handle_llm_subtask_outputs
```

```
cd /src/quantz/processing-server
cd tasks_server/service
. ./restart.sh handle_llm_outputs
```

```
cd /src/quantz/processing-server
cd tasks_server/service
. ./restart.sh respond
```

```
cd /src/quantz/processing-server
cd tasks_server/service
. ./restart.sh store_chatdata
```

workres general llm (handle_llm_general_task_outputs_worker, llm_general_task_worker)

```
cd /src/quantz/processing-server
cd tasks_server/service
. ./restart.sh general # restart all general llm services
```

```
cd /src/quantz/processing-server
cd tasks_server/service
. ./restart.sh llm_general_task
```

```
cd /src/quantz/processing-server
cd tasks_server/service
. ./restart.sh handle_llm_general_task_outputs
```

workers web tasks (billing_scheduler, process_chatdata)

```
cd /src/quantz/web-server/
cd web_tasks_server/service
. ./restart.sh all
```

```
cd /src/quantz/web-server/
cd web_tasks_server/service
. ./restart.sh billing_scheduler
```

```
cd /src/quantz/web-server/
cd web_tasks_server/service
. ./restart.sh process_chatdata
```

Logs workers (For each)

```
sudo journalctl -fu transcribe.service --output cat -n 1000 -f
```

```
sudo journalctl -fu handle_select_action.service --output cat -n 2000 -f
```

```
sudo journalctl -fu handle_llm_outputs.service --output cat -n 1000 -f
```

```
sudo journalctl -fu respond.service --output cat  -n 1000 -f
```

```
sudo journalctl -fu store_chatdata.service --output cat -n 1000 -f
```

```
sudo journalctl -fu llm_general_task.service --output cat -n 1000 -f
```

tts

```
ssh supercom3b
sudo journalctl -fu tts.service --output cat -n 1000 -f
```

Local DBs

status

```
cd /src/quantz/processing-server
docker ps
```

```
docker-compose logs -f rabbitmq_llm
```

```
telnet localhost 5672  # rabbitmq
telnet localhost 6381  # redis results llm
telnet localhost 6378  # redis results processing
```

Run

```
docker-compose up -d
```

processing-server/docker-compose.yml

```

services:
  rabbitmq_llm:

  redis_llm_result:  # for llm results

  redis_vectordb_result:  # for 

  redis_processing_result:  # for processing results

  redis_chatdb:  # for chat database with Unix socket
```

```
# RabbitMQ LLM 
RABBITMQ_LLM_USER=guest
RABBITMQ_LLM_HOST=localhost
RABBITMQ_LLM_PORT=5672
RABBITMQ_LLM_PASSWORD=<REDACTED>
RABBITMQ_LLM_DATA_PATH=/var/lib/rabbitmq
RABBITMQ_LLM_LOG_PATH=/var/log/rabbitmq

# Redis Results LLM
REDIS_RESULTS_LLM_HOST=localhost
REDIS_RESULTS_LLM_PORT=6381
REDIS_RESULTS_LLM_LOGLEVEL=debug
REDIS_RESULTS_LLM_DB_NUMBER=0
REDIS_RESULTS_LLM_EXPIRATION_TIME_SEC=180
REDIS_RESULTS_LLM_DATA_PATH=/var/lib/redis_llm

# Redis Results Processing
REDIS_RESULTS_PROCESSING_HOST=localhost
REDIS_RESULTS_PROCESSING_PORT=6378
REDIS_RESULTS_PROCESSING_LOGLEVEL=debug
REDIS_RESULTS_PROCESSING_DB_NUMBER=0
REDIS_RESULTS_PROCESSING_EXPIRATION_TIME_SEC=180
REDIS_RESULTS_PROCESSING_DATA_PATH=/var/lib/redis_processing

# Redis Local ChatDB
REDIS_LOCAL_CHATDB_ADDRESS=/tmp/redis_chatdb.sock
REDIS_LOCAL_CHATDB_DATA_PATH=/var/lib/redis_chatdb
REDIS_LOCAL_CHATDB_DB_NUMBER=0
```

Status

```
sudo systemctl status gateway-server
```

```
sudo systemctl status llm_server
```

```
sudo systemctl status unix_socket_server
```

running service list

```
systemctl list-units --type=service --state=running
```

Logrotate

```
sudo vim /etc/logrotate.d/rsyslog
```

check conf

```
sudo rsyslogd -N1
```

restart

```
 sudo systemctl restart rsyslog
```

最新の設定

```
/var/log/syslog
/var/log/mail.info
/var/log/mail.warn
/var/log/mail.err
/var/log/mail.log
/var/log/daemon.log
/var/log/kern.log
/var/log/auth.log
/var/log/user.log
/var/log/lpr.log
/var/log/cron.log
/var/log/debug
/var/log/messages
{
        rotate 7
        daily
        size 100M
        missingok
        notifempty
        compress
        delaycompress
        copytrancate
        sharedscripts
        postrotate
                /usr/lib/rsyslog/rsyslog-rotate
        endscript
}
```

Diskfull Supercom

Setup Daemon

gateway-server

/src/quantz/gateway-server/gateway-server.service

```
cd /src/quantz/gateway-server
. ./run_server.sh
```

```
sudo ln -s /src/quantz/gateway-server/gateway-server.service /etc/systemd/system/gateway-server.service
sudo systemctl daemon-reload
```

```
sudo systemctl enable gateway-server.service
sudo systemctl start gateway-server.service
```

```
sudo journalctl -fu gateway-server.service --output cat
```

*8001 already use

```
sudo netstat -tulnp | grep 8001
sudo kill {ps number}
```

unix_socket_server

/src/quantz/processing-server/unix_socket_server/unix_socket_server.service

```
rm /tmp/request.sock
cd /src/quantz/processing-server
cd unix_socket_server
python unix_socket_server.py
```

```
sudo ln -s /src/quantz/processing-server/unix_socket_server/unix_socket_server.service /etc/systemd/system/unix_socket_server.service
sudo systemctl daemon-reload
```

```
sudo systemctl enable unix_socket_server.service
sudo systemctl start unix_socket_server.service
```

```
sudo journalctl -fu unix_socket_server.service --output cat
```

llm

/src/quantz/processing-server/llm_server/llm_server.service

```
cd /src/quantz/processing-server
cd llm_server
python llm_server.py
```

```
sudo ln -s /src/quantz/processing-server/llm_server/llm_server.service /etc/systemd/system/llm_server.service
sudo systemctl daemon-reload
```

```
sudo systemctl enable llm_server.service
sudo systemctl start llm_server.service
```

```
sudo journalctl -fu llm_server.service --output cat
```

```
sudo journalctl -fu handle_llm_outputs.service --output cat -n 1000 -f
```

workers

/src/quantz/processing-server/task_server

logs

```
cd /src/quantz/processing-server/tasks_server/service
. ./service_logs.sh
```

*sudo apt-get update

sudo apt-get install multitail

symlink

```
sudo ln -s /src/quantz/processing-server/tasks_server/service/handle_llm_general_task_outputs.service /etc/systemd/system/handle_llm_general_task_outputs.service
sudo ln -s /src/quantz/processing-server/tasks_server/service/handle_llm_outputs.service /etc/systemd/system/handle_llm_outputs.service
sudo ln -s /src/quantz/processing-server/tasks_server/service/llm_general_task.service /etc/systemd/system/llm_general_task.service
sudo ln -s /src/quantz/processing-server/tasks_server/service/process_transcript.service /etc/systemd/system/process_transcript.service
sudo ln -s /src/quantz/processing-server/tasks_server/service/respond.service /etc/systemd/system/respond.service
sudo ln -s /src/quantz/processing-server/tasks_server/service/transcribe.service /etc/systemd/system/transcribe.service
```

```
sudo systemctl daemon-reload
sudo systemctl enable {}.service
sudo systemctl start {}.service
```

logs

```
sudo journalctl -fu transcribe.service --output cat
```

```
sudo journalctl -fu process_transcript.service --output cat
```

```
sudo journalctl -fu respond.service --output cat
```

```
sudo journalctl -fu llm_general_task.service --output cat  -n 1000 -f
```

```
sudo journalctl -fu handle_llm_general_task_outputs.service --output cat -n 1000 -f
```

transcribe

/src/quantz/processing-server/task_server/service/transcribe.service

```
cd /src/quantz/processing-server
WORKER_TYPE=transcribe GPU_ID=1 celery -A tasks_server.run:celery_app worker -l warning --concurrency=1 -Q transcribe
```

```
sudo ln -s /src/quantz/processing-server/tasks_server/service/transcribe.service /etc/systemd/system/transcribe.service
sudo systemctl daemon-reload
```

```
sudo systemctl enable transcribe_worker.service
sudo systemctl start transcribe.service
```

```
sudo journalctl -fu transcribe.service --output cat
```

process_transcript

/src/quantz/processing-server/task_server/service/process_transcript.service

```
cd /src/quantz/processing-server
WORKER_TYPE=process_transcript GPU_ID=1 celery -A tasks_server.run:celery_app worker -l warning --concurrency=1 -Q process_transcript
```

```
sudo ln -s /src/quantz/processing-server/tasks_server/service/process_transcript.service /etc/systemd/system/process_transcript.service
sudo systemctl daemon-reload
```

```
sudo systemctl enable process_transcript.service
sudo systemctl start process_transcript.service
```

```
sudo journalctl -fu process_transcript.service --output cat
```

handle_llm_outputs

/src/quantz/processing-server/task_server/service/handle_llm_output.service

```
cd /src/quantz/processing-server
WORKER_TYPE=handle_llm_outputs GPU_ID=1 celery -A tasks_server.run:celery_app worker -l warning --concurrency=1 -Q handle_llm_outputs
```

```
sudo ln -s /src/quantz/processing-server/tasks_server/service/handle_chat.service /etc/systemd/system/handle_chat.service
sudo systemctl daemon-reload
```

```
sudo systemctl enable handle_chat.service
sudo systemctl start handle_chat.service
```

```
sudo journalctl -fu handle_llm_outputs.service --output cat
```

respond

/src/quantz/processing-server/task_server/service/respond.service

```
cd /src/quantz/processing-server
WORKER_TYPE=respond GPU_ID=1 celery -A tasks_server.run:celery_app worker -l warning --concurrency=1 -Q respond
```

```
sudo ln -s /src/quantz/processing-server/tasks_server/service/respond.service /etc/systemd/system/respond.service
sudo systemctl daemon-reload
```

```
sudo systemctl enable respond.service
sudo systemctl start respond.service
```

```
sudo journalctl -fu respond.service --output cat
```

select_action

/src/quantz/processing-server/task_server/service/select_action.service

```
cd /src/quantz/processing-server
WORKER_TYPE=select_action GPU_ID=1 celery -A tasks_server.run:celery_app worker -l warning --concurrency=1 -Q select_action
```

```
sudo ln -s /src/quantz/processing-server/tasks_server/service/select_action.service /etc/systemd/system/select_action.service
sudo systemctl daemon-reload
```

```
sudo systemctl enable select_action.service
sudo systemctl start select_action.service
```

llm_subtask_outputs

/src/quantz/processing-server/task_server/service/handle_select_action.service

```
cd /src/quantz/processing-server
WORKER_TYPE=handle_llm_subtask_outputs GPU_ID=1 celery -A tasks_server.run:celery_app worker -l warning --concurrency=1 -Q handle_llm_subtask_outputs
```

```
sudo ln -s /src/quantz/processing-server/tasks_server/service/handle_select_action.service /etc/systemd/system/handle_select_action.service
sudo systemctl daemon-reload
```

```
sudo systemctl enable handle_select_action.service
sudo systemctl start handle_select_action.service
```

store_chatdata

```
cd /src/quantz/processing-server
WORKER_TYPE=store_chatdata celery -A tasks_server.run:celery_app worker -l warning --concurrency=1 -Q store_chatdata
```

```
sudo ln -s /src/quantz/processing-server/tasks_server/service/store_chatdata.service /etc/systemd/system/store_chatdata.service
sudo systemctl daemon-reload
```

```
sudo systemctl enable store_chatdata.service
sudo systemctl start store_chatdata.service
```

```
sudo journalctl -fu store_chatdata.service --output cat
```

handle_llm_general_task_outputs

/src/quantz/processing-server/task_server/service/handle_llm_general_task_outputs.service

```
cd /src/quantz/processing-server
WORKER_TYPE=handle_llm_general_task_outputs GPU_ID=1 celery -A tasks_server.run:celery_app worker -l warning --concurrency=1 -Q handle_llm_general_task_outputs
```

```
sudo ln -s /src/quantz/processing-server/tasks_server/service/handle_llm_general_task_outputs.service /etc/systemd/system/handle_llm_general_task_outputs.service
sudo systemctl daemon-reload
```

```
sudo systemctl enable handle_llm_general_task_outputs.service
sudo systemctl start handle_llm_general_task_outputs.service
```

```
sudo journalctl -fu handle_llm_general_task_outputs.service --output cat
```

llm_general_task

/src/quantz/processing-server/task_server/service/llm_general_task.service

```
cd /src/quantz/processing-server
WORKER_TYPE=llm_general_task GPU_ID=1 celery -A tasks_server.run:celery_app worker -l llwarning --concurrency=1 -Q title_keywords,sample_answer,review
```

```
sudo ln -s /src/quantz/processing-server/tasks_server/service/llm_general_task.service /etc/systemd/system/llm_general_task.service
sudo systemctl daemon-reload
```

```
sudo systemctl enable llm_general_task.service
sudo systemctl start llm_general_task.service
```

```
sudo journalctl -fu llm_general_task.service --output cat
```

vectordb_server

/src/quantz/vectordb_server/vectordb_server.service

```
cd /src/quantz/vectordb_server
celery -A run:celery_app worker -l info -Q echo,vectordb_save,vectordb_update,vectordb_delete,vectordb_delete_collection,vectordb_create_collection
```

```
sudo ln -s /src/quantz/vectordb_server/vectordb_server.service /etc/systemd/system/vectordb_server.service
sudo systemctl daemon-reload
```

```
sudo systemctl enable vectordb_server.service
sudo systemctl start vectordb_server.service
```

```
sudo journalctl -fu vectordb_server.service --output cat
```

billing_scheduler

/src/quantz/web-server/web_tasks_server/service/billing_scheduler.service

```
cd /src/quantz/web-server
cd web_tasks_server
WORKER_TYPE=billing celery -A run:celery_app worker -l info -Q billing.echo,billing.run_payment --hostname=billing_worker_1
```

```
sudo ln -s /src/quantz/web-server/web_tasks_server/service/billing_scheduler.service /etc/systemd/system/billing_scheduler.service
sudo systemctl daemon-reload
```

```
sudo systemctl enable billing_scheduler.service
sudo systemctl start billing_scheduler.service
```

process_chatdata

```
cd /src/quantz/web-server
cd web_tasks_server
WORKER_TYPE=process_chatdata celery -A run:celery_app worker -l info -Q process_chatdata --hostname=process_chatdata_worker_1
```

```
sudo ln -s /src/quantz/web-server/web_tasks_server/service/process_chatdata.service /etc/systemd/system/process_chatdata.service
sudo systemctl daemon-reload
```

```
sudo systemctl enable process_chatdata.service
sudo systemctl start process_chatdata.service
```
