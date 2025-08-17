#!/bin/bash

# NoteAI 本地开发环境启动脚本
# 使用方法: ./scripts/start-local.sh [选项]

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 显示帮助信息
show_help() {
    cat << EOF
NoteAI 本地开发环境启动脚本

使用方法:
    ./scripts/start-local.sh [选项]

选项:
    -h, --help          显示此帮助信息
    -s, --setup         初始化开发环境
    -d, --databases     仅启动数据库服务
    -u, --user          启动用户服务
    -a, --ai            启动AI服务
    -n, --note          启动笔记服务
    -A, --all           启动所有服务
    --install           安装Python依赖
    --check             检查环境配置

示例:
    ./scripts/start-local.sh --setup     # 初始化环境
    ./scripts/start-local.sh -d          # 仅启动数据库
    ./scripts/start-local.sh -A          # 启动所有服务

EOF
}

# 检查Python环境
check_python() {
    log_info "检查Python环境..."
    
    if ! command -v python3.12 &> /dev/null; then
        if ! command -v python3 &> /dev/null; then
            log_error "Python 3.12+ 未安装，请先安装Python"
            exit 1
        else
            PYTHON_CMD="python3"
        fi
    else
        PYTHON_CMD="python3.12"
    fi
    
    # 检查Python版本
    PYTHON_VERSION=$($PYTHON_CMD --version | cut -d' ' -f2)
    log_info "Python版本: $PYTHON_VERSION"
    
    # 检查虚拟环境
    if [ ! -d "venv" ]; then
        log_warning "虚拟环境不存在，正在创建..."
        $PYTHON_CMD -m venv venv
    fi
    
    # 激活虚拟环境
    source venv/bin/activate
    log_success "Python环境检查完成"
}

# 安装依赖
install_dependencies() {
    log_info "安装Python依赖..."
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 升级pip
    pip install --upgrade pip setuptools wheel
    
    # 安装项目依赖
    pip install -e .
    
    # 安装开发依赖
    pip install -e ".[dev]"
    
    log_success "依赖安装完成"
}

# 检查环境配置
check_environment() {
    log_info "检查环境配置..."
    
    # 检查.env文件
    if [ ! -f ".env" ]; then
        log_error ".env 文件不存在，请先创建配置文件"
        exit 1
    fi
    
    # 加载环境变量
    source .env
    
    # 检查关键配置
    if [ -z "$DEEPSEEK_API_KEY" ] || [ "$DEEPSEEK_API_KEY" = "your-deepseek-api-key-here" ]; then
        log_warning "DEEPSEEK_API_KEY 未配置，AI服务将无法正常工作"
    fi
    
    if [ -z "$JWT_SECRET_KEY" ] || [ "$JWT_SECRET_KEY" = "your-super-secret-jwt-key-change-in-production" ]; then
        log_warning "JWT_SECRET_KEY 使用默认值，生产环境请修改"
    fi
    
    log_success "环境配置检查完成"
}

# 启动数据库服务 (使用Docker)
start_databases() {
    log_info "启动数据库服务..."
    
    # 检查Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装，无法启动数据库服务"
        log_info "请手动安装并配置以下数据库:"
        echo "  - PostgreSQL (端口 5432)"
        echo "  - MongoDB (端口 27017)"
        echo "  - Redis (端口 6379)"
        echo "  - Elasticsearch (端口 9200)"
        return 1
    fi
    
    # 启动PostgreSQL
    if ! docker ps | grep -q noteai_postgres; then
        log_info "启动PostgreSQL..."
        docker run -d --name noteai_postgres \
            -e POSTGRES_DB=noteai_users \
            -e POSTGRES_USER=noteai \
            -e POSTGRES_PASSWORD=noteai_dev_pass \
            -p 5432:5432 \
            postgres:15
    fi
    
    # 启动MongoDB
    if ! docker ps | grep -q noteai_mongodb; then
        log_info "启动MongoDB..."
        docker run -d --name noteai_mongodb \
            -e MONGO_INITDB_ROOT_USERNAME=noteai \
            -e MONGO_INITDB_ROOT_PASSWORD=noteai_dev_pass \
            -p 27017:27017 \
            mongo:6
    fi
    
    # 启动Redis
    if ! docker ps | grep -q noteai_redis; then
        log_info "启动Redis..."
        docker run -d --name noteai_redis \
            -p 6379:6379 \
            redis:7-alpine redis-server --requirepass noteai_dev_pass
    fi
    
    # 启动Elasticsearch
    if ! docker ps | grep -q noteai_elasticsearch; then
        log_info "启动Elasticsearch..."
        docker run -d --name noteai_elasticsearch \
            -e "discovery.type=single-node" \
            -e "xpack.security.enabled=false" \
            -e "ES_JAVA_OPTS=-Xms512m -Xmx512m" \
            -p 9200:9200 \
            elasticsearch:8.11.0
    fi
    
    log_success "数据库服务启动完成"
    
    # 等待服务就绪
    log_info "等待数据库服务就绪..."
    sleep 10
}

# 启动用户服务
start_user_service() {
    log_info "启动用户服务..."
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 设置环境变量
    export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
    
    # 启动服务
    cd services/user_service
    uvicorn main:app --reload --host 0.0.0.0 --port 8001 &
    USER_SERVICE_PID=$!
    
    cd "$PROJECT_ROOT"
    log_success "用户服务已启动 (PID: $USER_SERVICE_PID, Port: 8001)"
}

# 启动AI服务
start_ai_service() {
    log_info "启动AI服务..."
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 设置环境变量
    export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
    
    # 启动服务
    cd services/ai_service
    uvicorn main:app --reload --host 0.0.0.0 --port 8002 &
    AI_SERVICE_PID=$!
    
    cd "$PROJECT_ROOT"
    log_success "AI服务已启动 (PID: $AI_SERVICE_PID, Port: 8002)"
}

# 启动笔记服务
start_note_service() {
    log_info "启动笔记服务..."
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 设置环境变量
    export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
    
    # 启动服务
    cd services/note_service
    uvicorn main:app --reload --host 0.0.0.0 --port 8003 &
    NOTE_SERVICE_PID=$!
    
    cd "$PROJECT_ROOT"
    log_success "笔记服务已启动 (PID: $NOTE_SERVICE_PID, Port: 8003)"
}

# 显示服务状态
show_status() {
    echo ""
    log_info "🎉 NoteAI 本地开发环境启动完成!"
    echo ""
    log_info "服务访问地址:"
    echo "  用户服务:       http://localhost:8001/docs"
    echo "  AI服务:         http://localhost:8002/docs"
    echo "  笔记服务:       http://localhost:8003/docs"
    echo ""
    log_info "健康检查:"
    echo "  用户服务:       http://localhost:8001/health"
    echo "  AI服务:         http://localhost:8002/health"
    echo "  笔记服务:       http://localhost:8003/health"
    echo ""
    log_info "停止服务: Ctrl+C 或运行 ./scripts/stop-local.sh"
    echo ""
}

# 等待服务
wait_for_services() {
    log_info "等待用户输入 Ctrl+C 停止服务..."
    
    # 创建停止脚本
    cat > scripts/stop-local.sh << 'EOF'
#!/bin/bash
echo "停止NoteAI本地服务..."

# 停止Python服务
pkill -f "uvicorn.*8001"
pkill -f "uvicorn.*8002" 
pkill -f "uvicorn.*8003"

# 停止Docker容器
docker stop noteai_postgres noteai_mongodb noteai_redis noteai_elasticsearch 2>/dev/null || true

echo "所有服务已停止"
EOF
    chmod +x scripts/stop-local.sh
    
    # 等待中断信号
    trap 'echo ""; echo "正在停止服务..."; ./scripts/stop-local.sh; exit 0' INT
    
    while true; do
        sleep 1
    done
}

# 主函数
main() {
    # 解析命令行参数
    SETUP=false
    DATABASES=false
    USER_SERVICE=false
    AI_SERVICE=false
    NOTE_SERVICE=false
    ALL_SERVICES=false
    INSTALL=false
    CHECK=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -s|--setup)
                SETUP=true
                shift
                ;;
            -d|--databases)
                DATABASES=true
                shift
                ;;
            -u|--user)
                USER_SERVICE=true
                shift
                ;;
            -a|--ai)
                AI_SERVICE=true
                shift
                ;;
            -n|--note)
                NOTE_SERVICE=true
                shift
                ;;
            -A|--all)
                ALL_SERVICES=true
                shift
                ;;
            --install)
                INSTALL=true
                shift
                ;;
            --check)
                CHECK=true
                shift
                ;;
            *)
                log_error "未知选项: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # 显示启动信息
    echo ""
    log_info "🚀 启动 NoteAI 本地开发环境"
    echo ""
    
    # 检查Python环境
    check_python
    
    # 安装依赖
    if [ "$INSTALL" = "true" ] || [ "$SETUP" = "true" ]; then
        install_dependencies
    fi
    
    # 检查环境配置
    if [ "$CHECK" = "true" ] || [ "$SETUP" = "true" ]; then
        check_environment
    fi
    
    # 启动数据库
    if [ "$DATABASES" = "true" ] || [ "$ALL_SERVICES" = "true" ] || [ "$SETUP" = "true" ]; then
        start_databases
    fi
    
    # 启动服务
    if [ "$USER_SERVICE" = "true" ] || [ "$ALL_SERVICES" = "true" ]; then
        start_user_service
    fi
    
    if [ "$AI_SERVICE" = "true" ] || [ "$ALL_SERVICES" = "true" ]; then
        start_ai_service
    fi
    
    if [ "$NOTE_SERVICE" = "true" ] || [ "$ALL_SERVICES" = "true" ]; then
        start_note_service
    fi
    
    # 如果启动了服务，显示状态并等待
    if [ "$ALL_SERVICES" = "true" ] || [ "$USER_SERVICE" = "true" ] || [ "$AI_SERVICE" = "true" ] || [ "$NOTE_SERVICE" = "true" ]; then
        show_status
        wait_for_services
    fi
    
    # 如果只是设置环境
    if [ "$SETUP" = "true" ] && [ "$ALL_SERVICES" = "false" ]; then
        echo ""
        log_success "环境设置完成！"
        log_info "使用 ./scripts/start-local.sh -A 启动所有服务"
    fi
}

# 执行主函数
main "$@"
