# **Architecture & Customization Guide**

## **1\. Executive Summary**

Welcome to the FastAPI LLM Starter Template\! This document is your guide to understanding the project's architecture, which is designed for both stability and easy customization.

The core principle is a clear separation between **reusable Infrastructure** and **replaceable Domain logic**. By understanding this distinction, you can confidently build your unique application on top of a robust, production-ready foundation.

This guide will walk you through:

* **Core Architectural Concepts**: The "why" behind the structure.  
* **Project Layout**: A tour of the key directories and their roles.  
* **Getting Started**: An actionable roadmap for customizing the template for your project.  
* **Extending the Infrastructure**: A guide for adding new, reusable technical capabilities.

## **2\. Core Architectural Concepts**

Our architecture is organized into functional layers that clearly separate concerns. The three most important concepts to understand are **Domain**, **Infrastructure**, and **Core**.

### **Domain Services 💼**

* **Definition**: This is your application's unique business logic. It answers the question, **"What does my application do?"**  
* **Location**: app/services/  
* **Purpose**: To implement the specific features and workflows that make your project unique. This layer is where you will spend most of your development time.  
* **Key Characteristics**:  
  * **Replaceable**: The example text\_processing\_service.py is meant to be deleted and replaced with your logic.  
  * **Composes Infrastructure**: It uses the stable services from the infrastructure/ layer to get work done (e.g., it uses the cache service, the AI client, etc.).  
  * **High Customization**: You will heavily modify and add files here.

### **Infrastructure Services 🏗️**

* **Definition**: These are the stable, reusable, business-agnostic technical capabilities that support your domain logic. They answer the question, **"HOW does my application do things?"**  
* **Location**: app/infrastructure/  
* **Purpose**: To provide a reliable, battle-tested library of tools like caching, resilience patterns, and security utilities.  
* **Key Characteristics**:  
  * **Stable**: You should rarely need to change the code in this directory. It's designed to be a solid foundation.  
  * **Business-Agnostic**: A caching service works the same way whether you're building a chatbot or a document analysis tool.  
  * **Low Customization**: You will configure these services (via core/config.py), but you won't often edit their code.

### **Core Application Setup ⚙️**

* **Definition**: This is the application's foundational setup and assembly code. It answers the question, **"How is my application put together?"**  
* **Location**: app/core/  
* **Purpose**: To handle application-wide concerns like configuration management and custom exception definitions.  
* **Key Characteristics**:  
  * **Project-Specific Foundation**: While the patterns are reusable, the specific contents (e.g., your project's unique configuration variables) are tailored to your application.  
  * **Moderate Customization**: You will modify files here when you start a new project to add settings or define custom errors, but you won't touch them frequently during feature development.

### **Dependency Direction**

The most important rule is the direction of dependencies. This ensures that your business logic can change without breaking the stable foundation.

Domain Services → Infrastructure Services → External Libraries  
(changeable) (stable) (managed)

## **3\. Project Structure Overview**

The backend codebase is organized to reflect these architectural principles. Here is a map of the key directories and their purpose:

backend/app/  
├── main.py                  \# FastAPI app setup, middleware, top-level routers  
├── dependencies.py          \# Global dependency injection functions  
│  
├── api/                     \# API Layer: Request/Response handling (thin layer)  
│   ├── v1/  
│   │   ├── text\_processing\_router.py \# Endpoints for the main business logic  
│   │   └── system\_router.py          \# /health, /operations, etc.  
│   ├── monitoring\_router.py      \# /monitoring/\* endpoints  
│   └── admin\_router.py           \# /admin/\* and /cache/\* endpoints  
│  
├── core/                    \# Application-wide setup & cross-cutting concerns  
│   ├── config.py              \# Centralized Pydantic settings  
│   └── exceptions.py          \# Custom exception classes  
│  
├── services/ (Domain)       \# Business-specific, replaceable logic  
│   └── text\_processing\_service.py \# Composes infrastructure to achieve a business goal  
│  
├── infrastructure/          \# Reusable, business-agnostic technical services  
│   ├── ai/                    \# AI provider abstractions, prompt building  
│   ├── cache/                 \# Caching logic and implementation  
│   ├── resilience/            \# Circuit breakers, retries, presets  
│   ├── security/              \# Auth, input/output validation logic  
│   └── monitoring/            \# Monitoring logic and metrics collection  
│  
└── schemas/                 \# Pydantic models (data contracts)  
    ├── text\_processing.py       \# Request/Response models for text processing  
    ├── monitoring.py            \# Models for monitoring endpoints  
    └── resilience.py            \# Models for resilience config endpoints

## **4\. Getting Started: Your Customization Roadmap**

This section provides a clear, step-by-step guide on where to make changes to adapt this template for your own project.

### **Step 1: Configure Your Project (core/config.py)**

This is the first place you should go.

* **Add Your Settings**: Add new fields to the Settings class for any API keys, feature flags, or other environment variables your application needs.  
* **Adjust Defaults**: Change default values for AI\_MODEL, RESILIENCE\_PRESET, etc., to match your project's requirements.  
* **Remove Unused Settings**: If you aren't using Redis, for example, you can remove the cache\_\* configuration fields to keep things clean.

### **Step 2: Define Your Business Logic (services/)**

This is where your unique application comes to life.

* **Delete the Example**: Start by deleting app/services/text\_processing\_service.py.  
* **Create Your Service(s)**: Create new Python files that contain the core logic of your application. These services will import and use the components from app/infrastructure/. For example, you might create invoicing\_service.py or document\_analysis\_service.py.

### **Step 3: Create Your Data Contracts (schemas/)**

Define the shape of your API's inputs and outputs.

* **Delete the Example**: You can remove app/schemas/text\_processing.py.  
* **Add Your Models**: Create new files with Pydantic models that define the request and response bodies for your API endpoints. This ensures data validation and generates accurate OpenAPI documentation.

### **Step 4: Expose Your Services via API (api/)**

Make your domain services accessible over HTTP.

* **Delete or Modify Routers**: Remove the example routers and create new ones that map HTTP endpoints (e.g., POST /invoices) to your new domain services.  
* **Keep System Routers**: The system\_router.py, monitoring\_router.py, and admin\_router.py are part of the template's infrastructure and can often be kept as-is.

### **Step 5: Define Custom Errors (core/exceptions.py)**

Give your application a clear error contract.

* **Add Domain Exceptions**: As you write your domain services, define specific exceptions for them here (e.g., InvoiceNotFoundError). These should inherit from the base exceptions provided in the file.  
* **Leave Base Exceptions Alone**: Do not modify the base ApplicationError or InfrastructureError, as these provide a consistent error handling foundation.

## **5\. Extending the Infrastructure**

As your application grows, you may need to add new technical capabilities, such as a database, a message queue, or more advanced monitoring. This section provides a guide for adding new components to the infrastructure/ layer correctly.

### **When to Add a New Infrastructure Service?**

First, determine if your new component truly belongs in the infrastructure/ layer. Ask these four questions:

1. **Is it Business-Agnostic?** Can it work without knowing the specific business rules of your application? (e.g., a database connection service doesn't care if it's storing users or products).  
2. **Is it Reusable?** Could multiple, different domain services potentially use this component? (e.g., both an orders\_service and a users\_service would need a database).  
3. **Is it Stable?** Will its core interface change infrequently? The *implementation* might change (e.g., swapping Postgres for MySQL), but the *methods* your domain services call should remain consistent (e.g., save\_record()).  
4. **Does it Solve a Technical Problem?** Does it handle a "how-to" problem (like "how to store data persistently" or "how to send an email") rather than a "what-to-do" business problem?

If you answer **YES** to all four, it's an infrastructure service.

### **How to Add a New Infrastructure Service: A Checklist**

Follow these steps to integrate a new infrastructure component cleanly. We'll use adding a **Supabase client for persistent storage** as an example.

#### **✅ Step 1: Create a New Subdirectory**

Create a new folder inside app/infrastructure/ that describes the component's function.

* **Example**: app/infrastructure/database/

#### **✅ Step 2: Implement the Service**

Inside the new directory, create a service.py file. This file will contain the class or functions that encapsulate the third-party library's logic.

* **Example**: Create app/infrastructure/database/service.py with a DatabaseService class.

\# app/infrastructure/database/service.py  
from supabase import create\_client, Client

class DatabaseService:  
    def \_\_init\_\_(self, url: str, key: str):  
        self.client: Client \= create\_client(url, key)

    async def get\_user\_by\_id(self, user\_id: int):  
        \# Encapsulate the Supabase-specific call  
        return self.client.table('users').select("\*").eq('id', user\_id).execute()

    \# Add other generic methods: save\_record, update\_record, etc.

#### **✅ Step 3: Add Configuration**

Add the required settings (API keys, URLs, etc.) to app/core/config.py. Your new service should be configured from this central file.

* **Example**: Add Supabase settings to the Settings class in app/core/config.py.

\# app/core/config.py  
class Settings(BaseSettings):  
    \# ... other settings  
    supabase\_url: str \= Field(default="", description="Supabase project URL")  
    supabase\_key: str \= Field(default="", description="Supabase public anon key")

#### **✅ Step 4: Create a Dependency Provider**

Make your new service available to the rest of the application using FastAPI's dependency injection system. Add a "getter" function to app/dependencies.py.

* **Example**: Add get\_database\_service to app/dependencies.py.

\# app/dependencies.py  
from functools import lru\_cache  
from .infrastructure.database.service import DatabaseService  
from .core.config import Settings

@lru\_cache()  
def get\_database\_service(settings: Settings \= Depends(get\_settings)) \-\> DatabaseService:  
    return DatabaseService(url=settings.supabase\_url, key=settings.supabase\_key)

#### **✅ Step 5: Use the Service in Your Domain Logic**

Now, your domain services can cleanly depend on the new infrastructure without knowing any of its implementation details.

* **Example**: Your domain service in app/services/ can now use the database.

\# app/services/your\_new\_service.py  
from fastapi import Depends  
from ..infrastructure.database.service import DatabaseService  
from ..dependencies import get\_database\_service

class YourService:  
    def \_\_init\_\_(self, db: DatabaseService \= Depends(get\_database\_service)):  
        self.db \= db

    async def get\_user\_profile(self, user\_id: int):  
        \# The domain service calls a simple, abstract method  
        user\_data \= await self.db.get\_user\_by\_id(user\_id)  
        \# ... process the data ...  
        return user\_profile

### **Example 2: Integrating OpenTelemetry for Grafana**

This follows the same pattern, even though it's not a client library.

1. **Directory**: app/infrastructure/telemetry/  
2. **Service**: app/infrastructure/telemetry/service.py could contain functions to configure the OTLP exporter and initialize tracing.  
3. **Configuration**: Add OTEL\_EXPORTER\_OTLP\_ENDPOINT to app/core/config.py.  
4. **Integration**: Instead of a dependency provider, you would call your telemetry setup function from within the application's lifespan manager in app/main.py.

By following this pattern, you keep your new technical capabilities isolated, reusable, and cleanly separated from your core business logic, making your application easier to maintain and scale.