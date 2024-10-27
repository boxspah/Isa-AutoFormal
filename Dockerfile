# 使用 Ubuntu 22.04 作为基础镜像
FROM ubuntu:22.04

ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 更新软件包列表并安装必要的工具
RUN apt-get update && \
    apt-get install -y \
    software-properties-common \
    wget \
    curl \
    gnupg \
    apt-transport-https \
    ca-certificates \
    sudo

# 安装 OpenJDK 11.0.21
RUN add-apt-repository ppa:openjdk-r/ppa && \
    apt-get update && \
    apt-get install -y openjdk-11-jdk

# 安装 Python 3.10.12
RUN apt-get install -y python3.10
RUN apt-get install -y python3-pip

# 设置默认的 Java 和 Python 版本
RUN update-alternatives --install /usr/bin/java java /usr/lib/jvm/java-11-openjdk-amd64/bin/java 1 && \
    update-alternatives --set java /usr/lib/jvm/java-11-openjdk-amd64/bin/java && \
    update-alternatives --install /usr/bin/javac javac /usr/lib/jvm/java-11-openjdk-amd64/bin/javac 1 && \
    update-alternatives --set javac /usr/lib/jvm/java-11-openjdk-amd64/bin/javac && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1 && \
    update-alternatives --set python3 /usr/bin/python3.10

# 输出 Java 版本
RUN java -version

# 输出 Python 版本
RUN python3 --version

# 清理缓存和不必要的软件包
RUN apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 下载并安装 Scala 2.13.8
ENV SCALA_VERSION=2.13.8
ENV SCALA_HOME=/usr/share/scala

RUN mkdir -p $SCALA_HOME && \
    wget "https://downloads.lightbend.com/scala/$SCALA_VERSION/scala-$SCALA_VERSION.tgz" && \
    tar -zxvf "scala-$SCALA_VERSION.tgz" -C $SCALA_HOME --strip-components=1 && \
    rm "scala-$SCALA_VERSION.tgz"

# 更新环境变量
ENV PATH=$PATH:$SCALA_HOME/bin

ENV SPARK_HOME=/usr/share/spark
RUN mkdir -p $SPARK_HOME && \
    wget -O "spark-3.5.0-bin-hadoop3-scala2.13.tgz" "https://dlcdn.apache.org/spark/spark-3.5.0/spark-3.5.0-bin-hadoop3-scala2.13.tgz" && \
    tar -zxvf "spark-3.5.0-bin-hadoop3-scala2.13.tgz" -C $SPARK_HOME --strip-components=1 && \
    rm "spark-3.5.0-bin-hadoop3-scala2.13.tgz"

# 添加sbt源到sources.list.d  
RUN echo "deb https://repo.scala-sbt.org/scalasbt/debian all main" | sudo tee /etc/apt/sources.list.d/sbt.list && \  
    echo "deb https://repo.scala-sbt.org/scalasbt/debian /" | sudo tee /etc/apt/sources.list.d/sbt_old.list  
  
# 导入sbt公钥以确保软件包的安全  
RUN curl -sL "https://keyserver.ubuntu.com/pks/lookup?op=get&search=0x2EE0EA64E40A89B84B2DF73499E82A75642AC823" | sudo apt-key add -  
  
# 更新软件包列表并安装sbt  
RUN sudo apt-get update && sudo apt-get install -y sbt  

RUN sbt --version

ENV ISABELLE_VERSION=Isabelle2023
ENV ISABELLE_HOME=/usr/share/Isabelle2023

RUN mkdir -p $ISABELLE_HOME
RUN dpkg --print-architecture | grep -q arm && \
    wget -O $ISABELLE_VERSION.tar.gz "https://isabelle.in.tum.de/website-Isabelle2023-RC1/dist/Isabelle2023-RC1_linux_arm.tar.gz" || \
    wget -O $ISABELLE_VERSION.tar.gz "https://isabelle.in.tum.de/website-Isabelle2023-RC1/dist/Isabelle2023-RC1_linux.tar.gz"

RUN tar -zxvf $ISABELLE_VERSION.tar.gz -C $ISABELLE_HOME --strip-components=1 && \
    rm $ISABELLE_VERSION.tar.gz


ENV OPENAI_API_KEY="<your_key>"

# 设置工作目录
WORKDIR /app
COPY . /app

RUN python3 -m pip install --no-cache-dir -r requirements.txt

# 定义默认命令
CMD ["bash"]
