::: app.main
    options:
        members:
            - root
            - health_check
            - auth_status
            - global_exception_handler
            - lifespan
        heading: "Main"

::: app.dependencies
    options:
        show_root_heading: true
        show_source: false
        heading: "Dependencies"