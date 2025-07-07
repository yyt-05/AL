document.addEventListener('DOMContentLoaded', function() {
    const player = document.getElementById('player');
    const ball = document.getElementById('ball');
    const powerLevel = document.getElementById('power-level');
    const powerText = document.getElementById('power-text');
    const gameContainer = document.getElementById('game-container');
    const basket = document.getElementById('basket');
    const message = document.getElementById('message');
    const scoreElement = document.getElementById('score');
    const successSound = document.getElementById('success-sound');
    
    let isCharging = false;
    let power = 0;
    let chargeInterval;
    let score = 0;
    let animationId = null;
    
    // 游戏初始化
    function init() {
        // 取消任何正在进行的动画
        if (animationId) {
            cancelAnimationFrame(animationId);
            animationId = null;
        }
        
        // 设置球初始位置
        ball.style.left = '250px';
        ball.style.bottom = '100px';
        ball.style.display = 'none';
        
        // 重置力度条
        powerLevel.style.height = '0%';
        powerText.textContent = '力度';
        
        // 隐藏消息
        message.style.opacity = '0';
        
        // 重置玩家姿势
        player.style.transform = 'translateY(0) scale(1) rotate(0deg)';
    }
    
    // 开始蓄力
    function startCharge() {
        if (isCharging) return;
        
        isCharging = true;
        ball.style.display = 'block';
        power = 0;
        
        // 鸡哥准备动作
        player.style.transform = 'translateY(-10px) scale(1.1)';
        
        chargeInterval = setInterval(function() {
            power += 2;
            if (power > 100) power = 100;
            
            powerLevel.style.height = power + '%';
            
            // 力度文字反馈
            if (power < 30) {
                powerText.textContent = '轻轻';
            } else if (power < 60) {
                powerText.textContent = '中等';
            } else if (power < 90) {
                powerText.textContent = '大力';
            } else {
                powerText.textContent = '超级！';
            }
        }, 50);
    }
    
    // 投篮
    function shoot() {
        if (!isCharging || animationId) return;
    
        clearInterval(chargeInterval);
        isCharging = false;
        player.style.transform = 'translateY(0) scale(1) rotate(-10deg)';
    
        // 篮筐参数（根据实际情况调整）
        const basketX = 700;      // 篮筐中心X坐标
        const basketY = 180;      // 篮筐最高点Y坐标
        const basketWidth = 60;   // 篮筐宽度
        const basketHeight = 40;  // 篮筐高度
    
        // 初始位置
        const startX = 250;
        const startY = 100;
    
        // 抛物线参数调整
        const angle = 55 * Math.PI / 180;  // 增大投篮角度
        const gravity = 0.1;              // 减小重力
        
        // 计算刚好无法命中的初速度（顶点略高于篮筐）
        const maxHeight = basketY + 30;  // 比篮筐高30px
        const requiredVy = Math.sqrt(2 * gravity * (maxHeight - startY));
        const requiredV0 = requiredVy / Math.sin(angle);
        
        // 根据power调整初速度（power=100时使用计算值）
        const initialVelocity = (power / 100) * requiredV0 * 0.95; // 乘以0.95确保无法命中
    
        let vx = initialVelocity * Math.cos(angle);
        let vy = initialVelocity * Math.sin(angle);
    
        let x = startX;
        let y = startY;
        let time = 0;
        let lastTime = performance.now();
    
        function animate(currentTime) {
            const deltaTime = (currentTime - lastTime) / 16;
            lastTime = currentTime;
            time += deltaTime * 0.5;
    
            // 更新位置
            x += vx * (1 - time * 0.001);
            y = startY + (vy * time) - (0.5 * gravity * time * time);
    
            ball.style.left = x + 'px';
            ball.style.bottom = y + 'px';
    
            // 碰撞检测（当power<100时才检测）
            if (power < 100) {
                const ballCenterX = x + 21;
                const ballCenterY = 500 - y - 21;
                
                if (ballCenterX > basketX - basketWidth/2 && 
                    ballCenterX < basketX + basketWidth/2 &&
                    ballCenterY > basketY - basketHeight/2 && 
                    ballCenterY < basketY + basketHeight/2) {
                    // 命中处理...
                }
            }
    
            // 出界检测...
            animationId = requestAnimationFrame(animate);
        }
    
        animationId = requestAnimationFrame(animate);
    }
    // 事件监听
    gameContainer.addEventListener('mousedown', startCharge);
    gameContainer.addEventListener('mouseup', shoot);
    gameContainer.addEventListener('mouseleave', function() {
        if (isCharging) {
            clearInterval(chargeInterval);
            isCharging = false;
            init();
        }
    });
    
    // 触摸设备支持
    gameContainer.addEventListener('touchstart', function(e) {
        e.preventDefault();
        startCharge();
    });
    
    gameContainer.addEventListener('touchend', function(e) {
        e.preventDefault();
        shoot();
    });
    
    // 初始化游戏
    init();
});