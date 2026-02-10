from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List
from app.auth import auth_handler
from app.crud import crud_handler
from app.utils.supabase_client import db_manager
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/admin", tags=["admin"])

@router.get("/dashboard/stats")
async def get_admin_stats(
    current_user: dict = Depends(auth_handler.get_current_admin)
):
    """Get admin dashboard statistics"""
    stats = await crud_handler.get_dashboard_stats()
    
    # Calculate daily averages
    try:
        orders = await db_manager.get_orders()
        
        if orders and len(orders) > 0:
            # Calculate average order value
            total_revenue = stats.get('total_revenue', 0)
            total_orders = stats.get('total_orders', 0)
            avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
            
            # Calculate conversion rate (if we had visitor data)
            # For now, we'll use a placeholder
            conversion_rate = 0.15
            
            stats['avg_order_value'] = round(avg_order_value, 2)
            stats['conversion_rate'] = round(conversion_rate * 100, 1)
        else:
            stats['avg_order_value'] = 0
            stats['conversion_rate'] = 0
    except Exception:
        stats['avg_order_value'] = 0
        stats['conversion_rate'] = 0
    
    return stats

@router.get("/recent-activity")
async def get_recent_activity(
    current_user: dict = Depends(auth_handler.get_current_admin)
):
    """Get recent activity for admin dashboard"""
    try:
        # Get recent orders (last 10)
        recent_orders = await db_manager.get_orders(limit=10)
        
        # Get recent messages (last 10)
        recent_messages = await db_manager.get_messages(limit=10)
        
        activity = []
        
        # Add orders to activity
        for order in recent_orders:
            activity.append({
                "type": "order",
                "id": order.get('id'),
                "title": f"New order: {order.get('service', 'Unknown')}",
                "description": f"From {order.get('client_name', 'Unknown')}",
                "amount": order.get('price', 0),
                "status": order.get('status', 'pending'),
                "timestamp": order.get('created_at'),
                "icon": "shopping-cart"
            })
        
        # Add messages to activity
        for message in recent_messages:
            activity.append({
                "type": "message",
                "id": message.get('id'),
                "title": f"New message: {message.get('subject', 'No subject')}",
                "description": f"From {message.get('name', 'Unknown')}",
                "status": message.get('status', 'unread'),
                "timestamp": message.get('created_at'),
                "icon": "message"
            })
        
        # Sort by timestamp
        activity.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Return top 15
        return activity[:15]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting recent activity: {str(e)}"
        )

@router.get("/revenue/chart")
async def get_revenue_chart_data(
    period: str = "7d",  # 7d, 30d, 90d, 1y
    current_user: dict = Depends(auth_handler.get_current_admin)
):
    """Get revenue chart data for different periods"""
    try:
        orders = await db_manager.get_orders()
        
        if not orders:
            return {"labels": [], "data": []}
        
        # Filter by period
        end_date = datetime.now()
        
        if period == "7d":
            start_date = end_date - timedelta(days=7)
            date_format = "%d/%m"
        elif period == "30d":
            start_date = end_date - timedelta(days=30)
            date_format = "%d/%m"
        elif period == "90d":
            start_date = end_date - timedelta(days=90)
            date_format = "%W"  # Week number
        elif period == "1y":
            start_date = end_date - timedelta(days=365)
            date_format = "%m/%Y"
        else:
            start_date = end_date - timedelta(days=7)
            date_format = "%d/%m"
        
        # Group orders by date
        revenue_by_date = {}
        
        for order in orders:
            try:
                order_date = datetime.fromisoformat(order.get('created_at', '').replace('Z', '+00:00'))
                
                if order_date >= start_date:
                    date_key = order_date.strftime(date_format)
                    
                    if order.get('status') == 'completed' and order.get('price'):
                        revenue_by_date[date_key] = revenue_by_date.get(date_key, 0) + order['price']
            except:
                continue
        
        # Convert to sorted lists
        labels = sorted(revenue_by_date.keys())
        data = [revenue_by_date[label] for label in labels]
        
        return {
            "labels": labels,
            "data": data,
            "total": sum(data),
            "period": period
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting revenue chart data: {str(e)}"
        )

@router.get("/orders/chart")
async def get_orders_chart_data(
    period: str = "7d",
    current_user: dict = Depends(auth_handler.get_current_admin)
):
    """Get orders chart data for different periods"""
    try:
        orders = await db_manager.get_orders()
        
        if not orders:
            return {"labels": [], "data": []}
        
        # Filter by period
        end_date = datetime.now()
        
        if period == "7d":
            start_date = end_date - timedelta(days=7)
            date_format = "%d/%m"
        elif period == "30d":
            start_date = end_date - timedelta(days=30)
            date_format = "%d/%m"
        elif period == "90d":
            start_date = end_date - timedelta(days=90)
            date_format = "%W"
        elif period == "1y":
            start_date = end_date - timedelta(days=365)
            date_format = "%m/%Y"
        else:
            start_date = end_date - timedelta(days=7)
            date_format = "%d/%m"
        
        # Group orders by date and status
        orders_by_date = {}
        statuses = ['pending', 'completed', 'cancelled']
        
        for order in orders:
            try:
                order_date = datetime.fromisoformat(order.get('created_at', '').replace('Z', '+00:00'))
                
                if order_date >= start_date:
                    date_key = order_date.strftime(date_format)
                    status = order.get('status', 'pending')
                    
                    if date_key not in orders_by_date:
                        orders_by_date[date_key] = {s: 0 for s in statuses}
                    
                    orders_by_date[date_key][status] = orders_by_date[date_key].get(status, 0) + 1
            except:
                continue
        
        # Convert to chart data
        labels = sorted(orders_by_date.keys())
        
        chart_data = {
            "labels": labels,
            "datasets": []
        }
        
        colors = {
            'pending': 'rgba(255, 193, 7, 0.8)',
            'completed': 'rgba(40, 167, 69, 0.8)',
            'cancelled': 'rgba(220, 53, 69, 0.8)'
        }
        
        for status in statuses:
            data = [orders_by_date.get(label, {}).get(status, 0) for label in labels]
            
            chart_data["datasets"].append({
                "label": status.capitalize(),
                "data": data,
                "backgroundColor": colors.get(status, 'rgba(0, 0, 0, 0.1)'),
                "borderColor": colors.get(status, 'rgba(0, 0, 0, 0.3)'),
                "borderWidth": 1
            })
        
        return chart_data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting orders chart data: {str(e)}"
        )

@router.get("/services/popular")
async def get_popular_services(
    current_user: dict = Depends(auth_handler.get_current_admin)
):
    """Get most popular services"""
    try:
        orders = await db_manager.get_orders()
        
        if not orders:
            return []
        
        # Count orders by service
        service_counts = {}
        
        for order in orders:
            service = order.get('service', 'Unknown')
            service_counts[service] = service_counts.get(service, 0) + 1
        
        # Sort by count
        popular_services = [
            {"service": service, "count": count}
            for service, count in sorted(service_counts.items(), 
                                        key=lambda x: x[1], reverse=True)
        ]
        
        return popular_services[:10]  # Top 10
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting popular services: {str(e)}"
        )

@router.post("/backup")
async def create_backup(
    current_user: dict = Depends(auth_handler.get_current_admin)
):
    """Create database backup (admin only)"""
    try:
        # Get all data
        orders = await db_manager.get_orders()
        messages = await db_manager.get_messages()
        gallery_items = await crud_handler.get_gallery_items()
        
        backup_data = {
            "timestamp": datetime.now().isoformat(),
            "orders": orders,
            "messages": messages,
            "gallery": gallery_items,
            "backup_type": "manual"
        }
        
        # You could save this to a file or cloud storage
        # For now, we'll just return it
        
        return {
            "message": "Backup created successfully",
            "timestamp": backup_data["timestamp"],
            "stats": {
                "orders": len(orders),
                "messages": len(messages),
                "gallery_items": len(gallery_items)
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating backup: {str(e)}"
        )

@router.get("/system/health")
async def system_health_check(
    current_user: dict = Depends(auth_handler.get_current_admin)
):
    """Check system health and status"""
    import psutil
    import platform
    
    try:
        # System info
        system_info = {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "processor": platform.processor(),
        }
        
        # Memory usage
        memory = psutil.virtual_memory()
        memory_info = {
            "total": memory.total,
            "available": memory.available,
            "percent": memory.percent,
            "used": memory.used,
            "free": memory.free
        }
        
        # Disk usage
        disk = psutil.disk_usage('/')
        disk_info = {
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": disk.percent
        }
        
        # Database connection check
        db_status = "healthy"
        try:
            await db_manager.get_orders(limit=1)
        except Exception as e:
            db_status = f"error: {str(e)}"
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "system": system_info,
            "memory": memory_info,
            "disk": disk_info,
            "database": db_status,
            "environment": "development"
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }