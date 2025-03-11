workspace {
    name "Online Store"
    !identifiers hierarchical

    model {
        user = Person "User"
        admin = Person "Admin"

        store = softwareSystem "E-Commerce Platform" {
            users_service = container "User Service" {
                technology "Python FastAPI"
                tags "auth"
                component "Authentication Management"
                component "User Profile Management"
            }

            product_service = container "Product Service" {
                technology "Python FastAPI"
                tags "product"
                component "Product Listing"
                component "Product Search"
                component "Product Recommendations"
                component "Product Management"
            }

            cart_service = container "Cart Service" {
                technology "Python FastAPI"
                tags "cart"
                component "Cart Item Management"
                component "Checkout Processing"
            }
            
            order_service = container "Order Service" {
                technology "Python FastAPI"
                tags "order"
                component "Order Placement"
                component "Order Tracking"
                component "Payment Processing"
            }
        }

        user -> store.users_service "Регистрация и аутентификация" "REST"
        user -> store.product_service "Просмотр товаров" "REST"
        user -> store.cart_service "Управление корзиной" "REST"
        user -> store.order_service "Оформление заказа" "REST"
        admin -> store.product_service "Управление товарами" "REST"
        admin -> store.order_service "Отслеживание заказов" "REST"
        
        store.cart_service -> store.order_service "Инициация оформления заказа" "REST"
        store.order_service -> store.order_service "Обработка платежа" "REST"
        store.order_service -> store.order_service "Обновление статуса заказа" "REST"
        
        store.product_service -> store.product_service "Обновление информации о товаре" "REST"
        store.product_service -> store.product_service "Удаление товара" "REST"
        store.product_service -> user "Товар отображается в каталоге" "REST"

        deploymentEnvironment "PROD" {
            deploymentNode "Cloud" {
                deploymentNode "Kubernetes Cluster" {
                    api_gateway = infrastructureNode "API Gateway"
                    db = infrastructureNode "PostgreSQL Database"
                    
                    users_pod = deploymentNode "users-pod" {
                        instances 3
                        containerInstance store.users_service
                    }
                    products_pod = deploymentNode "products-pod" {
                        instances 3
                        containerInstance store.product_service
                    }
                    cart_pod = deploymentNode "cart-pod" {
                        instances 3
                        containerInstance store.cart_service
                    }
                    orders_pod = deploymentNode "orders-pod" {
                        instances 3
                        containerInstance store.order_service
                    }
                    
                    api_gateway -> users_pod "Маршрутизация пользовательских запросов"
                    api_gateway -> products_pod "Маршрутизация запросов к товарам"
                    api_gateway -> cart_pod "Маршрутизация запросов к корзине"
                    api_gateway -> orders_pod "Маршрутизация запросов к заказам"
                    users_pod -> db "Хранение данных пользователей"
                    products_pod -> db "Хранение данных о товарах"
                    cart_pod -> db "Хранение данных корзины"
                    orders_pod -> db "Хранение данных заказов"
                }
            }
        }
    }

    views {
        themes default

        systemContext store "context" {
            include *
            exclude relationship.tag==video
            autoLayout
        }

        container store "containers" {
            include *
            autoLayout
        }

        component store.users_service "users_components" {
            include *
            autoLayout
        }

        component store.product_service "product_components" {
            include *
            autoLayout
        }

        component store.cart_service "cart_components" {
            include *
            autoLayout
        }
        
        component store.order_service "order_components" {
            include *
            autoLayout
        }

        deployment * "PROD" {
            include *
            autoLayout
        }

        dynamic store "order_flow" "Обработка заказа от корзины до завершения" {
            autoLayout lr
            user -> store.cart_service "Добавление товаров в корзину"
            store.cart_service -> store.order_service "Инициация оформления заказа"
            store.order_service -> store.order_service "Обработка платежа"
            store.order_service -> store.order_service "Обновление статуса заказа"
            store.order_service -> user "Подтверждение оформления заказа"
        }
        
        dynamic store "product_management" "Управление товарами администратором" {
            autoLayout lr
            admin -> store.product_service "Добавление нового товара"
            store.product_service -> store.product_service "Обновление информации о товаре"
            store.product_service -> user "Товар отображается в каталоге"
        }
    }
}
