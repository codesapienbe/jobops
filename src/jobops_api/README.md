# JobOps

A powerful Python application that automatically generates personalized motivation letters based on job descriptions from URLs, using various AI backends. 

## Required Port Configuration

The JobOps API requires the environment variable `JOBOPS_API_PORT` to be set before starting. There is no default port. If not set, the API will raise an error and refuse to start.

### Example

```bash
export JOBOPS_API_PORT=8081
python -m jobops_api
```

If not set, you will see:

```
RuntimeError: Environment variable JOBOPS_API_PORT must be set (no default port allowed).
``` 