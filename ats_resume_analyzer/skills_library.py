"""Skills library for ATS resume analysis."""

TECHNICAL_SKILLS = {
    # Programming Languages
    'programming_languages': [
        'Python', 'R', 'SQL', 'Java', 'JavaScript', 'TypeScript', 'C#', 'C++',
        'PHP', 'Ruby', 'Go', 'Scala', 'Swift', 'Kotlin', 'MATLAB', 'SAS',
        'VBA', 'Shell Scripting', 'Bash', 'PowerShell'
    ],
    
    # Database Technologies
    'databases': [
        'PostgreSQL', 'MySQL', 'Oracle', 'SQL Server', 'MongoDB', 'Redis',
        'Cassandra', 'DynamoDB', 'Snowflake', 'Redshift', 'BigQuery',
        'Teradata', 'Sybase', 'MariaDB', 'SQLite', 'Vertica', 'Presto',
        'Hive', 'Impala', 'Elasticsearch'
    ],
    
    # Business Intelligence Tools
    'bi_tools': [
        'Tableau', 'Power BI', 'Looker', 'Sisense', 'QlikView', 'QlikSense',
        'SAP BusinessObjects', 'MicroStrategy', 'IBM Cognos', 'Oracle BI',
        'Domo', 'Spotfire', 'Google Data Studio', 'Excel', 'ThoughtSpot',
        'Alteryx', 'Mode Analytics', 'Periscope Data', 'Metabase', 'Superset'
    ],
    
    # Data Engineering & ETL
    'data_engineering': [
        'dbt', 'Airflow', 'Informatica', 'SSIS', 'Talend', 'Pentaho',
        'Luigi', 'Dagster', 'Prefect', 'Fivetran', 'Stitch', 'Matillion',
        'AWS Glue', 'Azure Data Factory', 'Google Cloud Dataflow',
        'Spark', 'Hadoop', 'Kafka', 'NiFi', 'StreamSets'
    ],
    
    # Cloud Platforms & Services
    'cloud_services': [
        'AWS', 'Azure', 'Google Cloud', 'AWS RDS', 'AWS S3', 'AWS Lambda',
        'AWS EMR', 'Azure Synapse', 'Azure Databricks', 'GCP BigQuery',
        'AWS CloudFormation', 'Terraform', 'Docker', 'Kubernetes', 'ECS',
        'Azure Functions', 'Cloud Formation', 'AWS SageMaker', 'Databricks'
    ],
    
    # Data Science & Analytics
    'data_science': [
        'Machine Learning', 'Statistical Analysis', 'Predictive Modeling',
        'A/B Testing', 'Regression Analysis', 'Time Series Analysis',
        'Clustering', 'Classification', 'Natural Language Processing',
        'Deep Learning', 'Neural Networks', 'Random Forest', 'XGBoost',
        'Feature Engineering', 'Hypothesis Testing', 'Dimensionality Reduction',
        'Forecasting', 'Optimization', 'Data Mining', 'Text Analytics'
    ],
    
    # Data Visualization
    'data_visualization': [
        'D3.js', 'Plotly', 'Matplotlib', 'Seaborn', 'ggplot2',
        'Highcharts', 'Chart.js', 'Bokeh', 'Grafana', 'Kibana',
        'Google Charts', 'Vega', 'Observable', 'Dash', 'Shiny'
    ],
    
    # Version Control & Development Tools
    'development_tools': [
        'Git', 'GitHub', 'GitLab', 'Bitbucket', 'JIRA', 'Confluence',
        'Jenkins', 'Travis CI', 'CircleCI', 'Azure DevOps', 'Maven',
        'Gradle', 'npm', 'Webpack', 'VS Code', 'PyCharm', 'IntelliJ',
        'Eclipse', 'Jupyter', 'RStudio'
    ],
    
    # Inventory & Supply Chain
    'inventory_systems': [
        'SAP', 'Oracle SCM', 'JDA', 'Manhattan Associates', 'NetSuite',
        'Epicor', 'Microsoft Dynamics', 'Sage', 'IFS', 'Blue Yonder',
        'Infor', 'HighJump', 'Red Prairie', 'ASCTrac', 'TradeGecko',
        'Fishbowl', 'QuickBooks Enterprise', 'Zoho Inventory', 'Odoo'
    ],
    
    # Data Formats & APIs
    'data_formats_apis': [
        'JSON', 'XML', 'CSV', 'Parquet', 'Avro', 'ORC', 'REST APIs',
        'GraphQL', 'SOAP', 'gRPC', 'Protobuf', 'WebSocket', 'OAuth',
        'JWT', 'YAML', 'HTML', 'CSS', 'Markdown', 'LaTeX'
    ],
    
    # Testing & Quality Assurance
    'testing': [
        'Unit Testing', 'Integration Testing', 'Pytest', 'JUnit',
        'Selenium', 'TestNG', 'Mocha', 'Jest', 'Cypress', 'Robot Framework',
        'Load Testing', 'Performance Testing', 'TDD', 'BDD', 'QA Automation'
    ]
}

SOFT_SKILLS = {
    # Leadership & Management
    'leadership': [
        'Team Leadership', 'Project Management', 'Strategic Planning',
        'Decision Making', 'Change Management', 'Risk Management',
        'Stakeholder Management', 'Resource Planning', 'Team Building',
        'Mentoring', 'Coaching', 'Performance Management'
    ],
    
    # Communication
    'communication': [
        'Verbal Communication', 'Written Communication', 'Presentation Skills',
        'Technical Writing', 'Public Speaking', 'Client Communication',
        'Cross-functional Communication', 'Executive Communication',
        'Documentation', 'Requirements Gathering', 'Status Reporting'
    ],
    
    # Problem Solving
    'problem_solving': [
        'Analytical Thinking', 'Critical Thinking', 'Problem Analysis',
        'Root Cause Analysis', 'Troubleshooting', 'Decision Making',
        'Innovation', 'Creative Problem Solving', 'Systems Thinking',
        'Process Improvement', 'Solution Design'
    ],
    
    # Collaboration
    'collaboration': [
        'Team Collaboration', 'Cross-functional Collaboration',
        'Stakeholder Engagement', 'Relationship Building',
        'Conflict Resolution', 'Team Building', 'Partnership Development',
        'Knowledge Sharing', 'Mentoring', 'Peer Review'
    ],
    
    # Business Acumen
    'business_skills': [
        'Business Analysis', 'Requirements Analysis', 'Process Optimization',
        'Strategic Thinking', 'Business Strategy', 'Industry Knowledge',
        'Market Analysis', 'Financial Analysis', 'Cost-Benefit Analysis',
        'ROI Analysis', 'Budgeting', 'Forecasting'
    ],
    
    # Project Management
    'project_skills': [
        'Agile Methodologies', 'Scrum', 'Kanban', 'Waterfall',
        'Sprint Planning', 'Release Management', 'Resource Allocation',
        'Timeline Management', 'Risk Assessment', 'Scope Management',
        'Project Coordination', 'Milestone Tracking'
    ]
}

EXPERIENCE_KEYWORDS = [
    # Action Verbs
    'Developed', 'Implemented', 'Designed', 'Analyzed', 'Optimized',
    'Led', 'Managed', 'Coordinated', 'Created', 'Established',
    'Improved', 'Enhanced', 'Streamlined', 'Automated', 'Architected',
    'Deployed', 'Maintained', 'Monitored', 'Resolved', 'Troubleshot',
    'Researched', 'Evaluated', 'Assessed', 'Recommended', 'Presented',
    'Collaborated', 'Partnered', 'Facilitated', 'Guided', 'Mentored',
    
    # Impact Words
    'Increased', 'Decreased', 'Reduced', 'Improved', 'Saved',
    'Generated', 'Achieved', 'Delivered', 'Launched', 'Transformed',
    'Accelerated', 'Simplified', 'Enhanced', 'Maximized', 'Minimized',
    
    # Metrics
    'ROI', 'Revenue', 'Cost Savings', 'Efficiency', 'Performance',
    'Productivity', 'Quality', 'Customer Satisfaction', 'Time to Market',
    'Market Share', 'Growth', 'Adoption Rate', 'Success Rate'
]

EDUCATION_KEYWORDS = [
    # Degrees
    'Bachelor', 'Master', 'PhD', 'MBA', 'Associates',
    'BS', 'BA', 'MS', 'MA', 'BSc', 'MSc', 'BBA', 'MCA',
    
    # Fields
    'Computer Science', 'Information Technology', 'Data Science',
    'Business Analytics', 'Statistics', 'Mathematics',
    'Information Systems', 'Software Engineering', 'Business Administration',
    'Supply Chain Management', 'Operations Research',
    
    # Certifications
    'AWS Certified', 'Microsoft Certified', 'Google Certified',
    'PMP', 'Scrum', 'CISSP', 'CISA', 'ITIL', 'Six Sigma',
    'CPIM', 'CSCP', 'CLTD', 'CompTIA', 'Oracle Certified'
]

FORMATTING_GUIDELINES = {
    'section_headers': [
        'Summary', 'Experience', 'Education', 'Skills', 'Projects',
        'Certifications', 'Publications', 'Awards', 'Languages',
        'Volunteer Work', 'Professional Development'
    ],
    'preferred_fonts': [
        'Arial', 'Calibri', 'Helvetica', 'Times New Roman',
        'Garamond', 'Georgia', 'Verdana', 'Tahoma'
    ],
    'bullet_points': ['•', '-', '∙'],
    'date_formats': [
        'MM/YYYY', 'YYYY', 'MM-YYYY',
        'Month YYYY', 'YYYY-Present'
    ]
}
