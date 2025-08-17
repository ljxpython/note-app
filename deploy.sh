#!/bin/bash
# NoteAI 部署脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# 检查依赖
check_dependencies() {
    log_info "检查系统依赖..."
    
    # 检查Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请先安装Docker"
        exit 1
    fi
    
    # 检查Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose未安装，请先安装Docker Compose"
        exit 1
    fi
    
    log_success "依赖检查通过"
}

# 环境配置
setup_environment() {
    log_info "设置环境配置..."
    
    if [ ! -f .env ]; then
        log_warning ".env文件不存在，从模板创建..."
        cp .env.example .env
        log_info "请编辑 .env 文件配置您的环境变量"
        log_info "特别注意修改 JWT_SECRET_KEY 和其他敏感信息"
    fi
    
    log_success "环境配置完成"
}

# 构建镜像
build_images() {
    log_info "构建Docker镜像..."
    
    if command -v docker-compose &> /dev/null; then
        docker-compose build
    else
        docker compose build
    fi
    
    log_success "镜像构建完成"
}

# 启动服务
start_services() {
    log_info "启动服务..."
    
    if command -v docker-compose &> /dev/null; then
        docker-compose up -d
    else
        docker compose up -d
    fi
    
    log_success "服务启动完成"
}

# 等待服务就绪
wait_for_services() {
    log_info "等待服务就绪..."
    
    # 等待后端服务
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s http://localhost:8000/health > /dev/null; then
            log_success "后端服务就绪"
            break
        fi
        
        log_info "等待后端服务启动... ($attempt/$max_attempts)"
        sleep 2
        ((attempt++))
    done
    
    if [ $attempt -gt $max_attempts ]; then
        log_error "后端服务启动超时"
        return 1
    fi
    
    # 等待前端服务
    attempt=1
    while [ $attempt -le $max_attempts ]; do
        if curl -s http://localhost:3000 > /dev/null; then
            log_success "前端服务就绪"
            break
        fi
        
        log_info "等待前端服务启动... ($attempt/$max_attempts)"
        sleep 2
        ((attempt++))
    done
    
    if [ $attempt -gt $max_attempts ]; then
        log_error "前端服务启动超时"
        return 1
    fi
}

# 健康检查
health_check() {
    log_info "执行健康检查..."
    
    # 检查后端健康状态
    local health_response=$(curl -s http://localhost:8000/health)
    if echo "$health_response" | grep -q '"status":"healthy"'; then
        log_success "后端健康检查通过"
    else
        log_error "后端健康检查失败"
        return 1
    fi
    
    # 检查前端
    if curl -s http://localhost:3000 > /dev/null; then
        log_success "前端健康检查通过"
    else
        log_error "前端健康检查失败"
        return 1
    fi
}

# 显示服务信息
show_service_info() {
    log_success "🎉 NoteAI部署成功！"
    echo ""
    echo "📱 访问地址:"
    echo "   前端应用: http://localhost:3000"
    echo "   后端API:  http://localhost:8000"
    echo "   API文档:  http://localhost:8000/docs"
    echo ""
    echo "🔑 默认管理员账号:"
    echo "   邮箱: admin@noteai.com"
    echo "   密码: AdminPass123!"
    echo ""
    echo "🛠️ 管理命令:"
    echo "   查看日志: docker-compose logs -f"
    echo "   停止服务: docker-compose down"
    echo "   重启服务: docker-compose restart"
    echo ""
    echo "⚠️  生产环境提醒:"
    echo "   1. 修改默认密码"
    echo "   2. 配置HTTPS"
    echo "   3. 设置防火墙"
    echo "   4. 定期备份数据"
}

# 清理函数
cleanup() {
    log_info "清理资源..."
    if command -v docker-compose &> /dev/null; then
        docker-compose down
    else
        docker compose down
    fi
}

# 主函数
main() {
    echo "🚀 NoteAI 自动部署脚本"
    echo "========================"
    
    # 解析命令行参数
    case "${1:-deploy}" in
        "deploy")
            check_dependencies
            setup_environment
            build_images
            start_services
            wait_for_services
            health_check
            show_service_info
            ;;
        "build")
            check_dependencies
            build_images
            ;;
        "start")
            start_services
            wait_for_services
            health_check
            show_service_info
            ;;
        "stop")
            cleanup
            log_success "服务已停止"
            ;;
        "restart")
            cleanup
            start_services
            wait_for_services
            health_check
            show_service_info
            ;;
        "health")
            health_check
            ;;
        *)
            echo "用法: $0 [deploy|build|start|stop|restart|health]"
            echo ""
            echo "命令说明:"
            echo "  deploy   - 完整部署 (默认)"
            echo "  build    - 仅构建镜像"
            echo "  start    - 启动服务"
            echo "  stop     - 停止服务"
            echo "  restart  - 重启服务"
            echo "  health   - 健康检查"
            exit 1
            ;;
    esac
}

# 捕获中断信号
trap cleanup EXIT

# 执行主函数
main "$@"
