# AuditAgent Evaluation Report

**Passed:** 9/9
**Pass rate:** 100.00%

| ID | Question | Expected Route | Actual Route | Verification | Result |
|---|---|---|---|---|---|
| doc_001 | What was the company revenue in Q1 2026? | document | document | SUPPORTED | PASS |
| doc_002 | What is the expected revenue growth for the next quarter? | document | document | SUPPORTED | PASS |
| doc_003 | What employee benefits does the company provide? | document | document | SUPPORTED | PASS |
| doc_004 | How many annual leave days are employees entitled to? | document | document | SUPPORTED | PASS |
| acl_001 | What employee benefits does the company provide? | document | document | None | PASS |
| acl_002 | What was the company revenue in Q1 2026? | document | document | None | PASS |
| sql_001 | How many employees are in the Finance department? | sql | sql | SUPPORTED | PASS |
| sql_002 | What is the budget of the HR department? | sql | sql | SUPPORTED | PASS |
| web_001 | What is Python? | web | web | SUPPORTED | PASS |

## Detailed Results

### doc_001

**Question:** What was the company revenue in Q1 2026?

**Expected route:** document

**Actual route:** document

**Verification:** SUPPORTED

**Answer:**

The company reported revenue of **INR 48.5 crore** in Q1 2026【finance.txt – Document 1】.

### doc_002

**Question:** What is the expected revenue growth for the next quarter?

**Expected route:** document

**Actual route:** document

**Verification:** SUPPORTED

**Answer:**

The finance department expects revenue to grow by **approximately 8 percent** in the next quarter【finance.txt – Document 1】.

### doc_003

**Question:** What employee benefits does the company provide?

**Expected route:** document

**Actual route:** document

**Verification:** SUPPORTED

**Answer:**

The company provides the following employee benefits:

- **Medical insurance**  
- **Paid leave** (the standard annual entitlement is 24 days, with the option to request additional unpaid leave)【hr.txt – Document 1】【hr.txt – Document 3】  
- **Retirement benefits**【hr.txt – Document 1】

### doc_004

**Question:** How many annual leave days are employees entitled to?

**Expected route:** document

**Actual route:** document

**Verification:** SUPPORTED

**Answer:**

Employees are entitled to **24 days of annual leave** per year. 【hr.txt – Document 1】

### acl_001

**Question:** What employee benefits does the company provide?

**Expected route:** document

**Actual route:** document

**Verification:** None

**Answer:**

I cannot provide a reliable answer from the available authorized evidence.

### acl_002

**Question:** What was the company revenue in Q1 2026?

**Expected route:** document

**Actual route:** document

**Verification:** None

**Answer:**

I cannot provide a reliable answer from the available authorized evidence.

### sql_001

**Question:** How many employees are in the Finance department?

**Expected route:** sql

**Actual route:** sql

**Verification:** SUPPORTED

**Answer:**

The query `SELECT COUNT(*) FROM employees WHERE department = 'Finance';` returned a count of **2**, so there are **2 employees** in the Finance department.

### sql_002

**Question:** What is the budget of the HR department?

**Expected route:** sql

**Actual route:** sql

**Verification:** SUPPORTED

**Answer:**

The SQL query returns a single value for the HR department’s budget:

- **Budget:** 12.5 crore  

(From the query `SELECT budget_crore FROM departments WHERE department = 'HR';` which returned `[(12.5,)]`.)

### web_001

**Question:** What is Python?

**Expected route:** web

**Actual route:** web

**Verification:** SUPPORTED

**Answer:**

**Python** is an interpreted, high‑level, general‑purpose programming language.  

- It is **object‑oriented** and uses **dynamic typing and dynamic binding**, which makes it well‑suited for rapid application development and for “glue” scripting that connects existing components 【1】.  
- The language emphasizes a **simple, readable syntax** (English‑like words, indentation instead of braces) that lowers the learning curve and speeds the edit‑test‑debug cycle 【1】【4】.  
- Python’s standard library and extensive third‑party modules are freely available for all major platforms, allowing developers to write server‑side code, web applications, desktop/mobile apps, data‑analysis pipelines, machine‑learning models, cloud automation, and many other tasks 【2】【3】【4】.  

In short, Python is a versatile, easy‑to‑learn, interpreted language that can be used for everything from web and software development to data science and automation.  

**Sources**  
- Python.org executive summary 【1】  
- Southern New Hampshire University overview 【2】  
- Coursera beginner’s guide 【3】  
- AWS “What is Python?” page 【4】
