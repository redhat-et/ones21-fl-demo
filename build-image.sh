IMAGE=${FL_IMAGE:-"ibm-fl-lib:latest"}

docker build -t ${IMAGE} ./federated-learning-lib/ -f Dockerfile.37
