# math_edu_chatbot documentation!

## Description

The Classroom Cloud (Local Client-Server)

## Commands

The Makefile contains the central entry points for common tasks related to this project.

### Syncing data to cloud storage

* `make sync_data_up` will use `gsutil rsync` to recursively sync files in `data/` up to `gs://bucket-name/data/`.
* `make sync_data_down` will use `gsutil rsync` to recursively sync files in `gs://bucket-name/data/` to `data/`.


