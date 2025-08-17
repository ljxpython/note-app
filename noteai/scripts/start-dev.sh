#!/bin/bash

# NoteAI 开发环境启动脚本
# 使用方法: ./scripts/start-dev.sh [选项]

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
NoteAI 开发环境启动脚本

使用方法:
    ./scripts/start-dev.sh [选项]

选项:
    -h, --help          显示此帮助信息
    -c, --clean         清理并重新构建容器
    -d, --detach        后台运行
    -t, --tools         启动开发工具 (Adminer, Mongo Express, Redis Commander)
    -s, --services      仅启动指定服务 (用逗号分隔)
    --no-build          不重新构建镜像
    --logs              显示服务日志
    --status            显示服务状态

示例:
    ./scripts/start-dev.sh                    # 启动所有服务
    ./scripts/start-dev.sh -c                # 清理并重新启动
    ./scripts/start-dev.sh -t                # 启动服务和开发工具
    ./scripts/start-dev.sh -s user-service   # 仅启动用户服务
    ./scripts/start-dev.sh --logs            # 显示日志

EOF
}

# 检查依赖
check_dependencies() {
    log_info "检查依赖..."
    
    # 检查Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi
    
    # 检查Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose 未安装，请先安装 Docker Compose"
        exit 1
    fi
    
    # 检查.env文件
    if [ ! -f ".env" ]; then
        log_warning ".env 文件不存在，从 .env.example 复制..."
        cp .env.example .env
        log_warning "请编辑 .env 文件并填入正确的配置值"
    fi
    
    log_success "依赖检查完成"
}

# 清理环境
clean_environment() {
    log_info "清理开发环境..."
    
    # 停止并删除容器
    docker-compose -f docker-compose.dev.yml down -v --remove-orphans
    
    # 删除镜像 (可选)
    if [ "$CLEAN_IMAGES" = "true" ]; then
        log_info "删除旧镜像..."
        docker-compose -f docker-compose.dev.yml down --rmi all
    fi
    
    # 清理未使用的资源
    docker system prune -f
    
    log_success "环境清理完成"
}

# 构建服务
build_services() {
    log_info "构建服务镜像..."
    
    if [ "$NO_BUILD" = "true" ]; then
        log_info "跳过镜像构建"
        return
    fi
    
    # 构建所有服务镜像
    docker-compose -f docker-compose.dev.yml build --parallel
    
    log_success "服务镜像构建完成"
}

# 启动服务
start_services() {
    log_info "启动服务..."
    
    # 构建启动命令
    local cmd="docker-compose -f docker-compose.dev.yml up"
    
    # 添加选项
    if [ "$DETACH" = "true" ]; then
        cmd="$cmd -d"
    fi
    
    if [ "$TOOLS" = "true" ]; then
        cmd="$cmd --profile tools"
    fi
    
    if [ -n "$SERVICES" ]; then
        cmd="$cmd $SERVICES"
    fi
    
    # 执行启动命令
    eval $cmd
    
    if [ "$DETACH" = "true" ]; then
        log_success "服务已在后台启动"
        show_service_status
    fi
}

# 显示服务状态
show_service_status() {
    log_info "服务状态:"
    docker-compose -f docker-compose.dev.yml ps
    
    echo ""
    log_info "服务访问地址:"
    echo "  API网关:        http://localhost:8000"
    echo "  用户服务:       http://localhost:8001"
    echo "  AI服务:         http://localhost:8002"
    echo "  笔记服务:       http://localhost:8003"
    echo ""
    echo "  数据库管理工具:"
    echo "  Adminer:        http://localhost:8080"
    echo "  Mongo Express:  http://localhost:8081 (admin/admin123)"
    echo "  Redis Commander: http://localhost:8082"
}

# 显示日志
show_logs() {
    log_info "显示服务日志..."
    
    if [ -n "$SERVICES" ]; then
        docker-compose -f docker-compose.dev.yml logs -f $SERVICES
    else
        docker-compose -f docker-compose.dev.yml logs -f
    fi
}

# 等待服务就绪
wait_for_services() {
    log_info "等待服务就绪..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        log_info "检查服务状态 ($attempt/$max_attempts)..."
        
        # 检查关键服务
        local all_healthy=true
        
        # 检查数据库
        if ! docker-compose -f docker-compose.dev.yml exec -T postgres pg_isready -U noteai -d noteai_users &> /dev/null; then
            all_healthy=false
        fi
        
        # 检查MongoDB
        if ! docker-compose -f docker-compose.dev.yml exec -T mongodb mongosh --eval "db.adminCommand('ping')" &> /dev/null; then
            all_healthy=false
        fi
        
        # 检查Redis
        if ! docker-compose -f docker-compose.dev.yml exec -T redis redis-cli ping &> /dev/null; then
            all_healthy=false
        fi
        
        if [ "$all_healthy" = "true" ]; then
            log_success "所有服务已就绪"
            return 0
        fi
        
        sleep 5
        ((attempt++))
    done
    
    log_warning "部分服务可能未完全就绪，请检查日志"
    return 1
}

# 主函数
main() {
    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -c|--clean)
                CLEAN=true
                shift
                ;;
            -d|--detach)
                DETACH=true
                shift
                ;;
            -t|--tools)
                TOOLS=true
                shift
                ;;
            -s|--services)
                SERVICES="$2"
                shift 2
                ;;
            --no-build)
                NO_BUILD=true
                shift
                ;;
            --logs)
                SHOW_LOGS=true
                shift
                ;;
            --status)
                SHOW_STATUS=true
                shift
                ;;
            --clean-images)
                CLEAN_IMAGES=true
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
    log_info "🚀 启动 NoteAI 开发环境"
    echo ""
    
    # 检查依赖
    check_dependencies
    
    # 仅显示状态
    if [ "$SHOW_STATUS" = "true" ]; then
        show_service_status
        exit 0
    fi
    
    # 仅显示日志
    if [ "$SHOW_LOGS" = "true" ]; then
        show_logs
        exit 0
    fi
    
    # 清理环境
    if [ "$CLEAN" = "true" ]; then
        clean_environment
    fi
    
    # 构建服务
    build_services
    
    # 启动服务
    start_services
    
    # 如果是后台运行，等待服务就绪
    if [ "$DETACH" = "true" ]; then
        wait_for_services
        
        echo ""
        log_success "🎉 NoteAI 开发环境启动完成!"
        echo ""
        log_info "使用以下命令管理服务:"
        echo "  查看状态: ./scripts/start-dev.sh --status"
        echo "  查看日志: ./scripts/start-dev.sh --logs"
        echo "  停止服务: docker-compose -f docker-compose.dev.yml down"
        echo ""
    fi
}

# 执行主函数
main "$@"
