# Databricks Bundles, Serverless Jobs, and CI/CD Guide

## Intention

I have made this document to cover some of the concepts I have encountered during the Databricks bundle and CI/CD implementation increment of the project. The intention is to go into more detail into certain core ideas to solidify my own learning and so the reader can follow the accociated runbooks and other documentation produced at this stage.

## The Issue This Development Increment Addresses

Before this phase of development, I had already established the core infrastructural architecture using terraform. In summary I had:

```txt
Azure
    resource group
    storage account
    Databricks Access Connector
    RBAC

Databricks / Unity Catalog
    storage credential
    external locations
    catalog
    schema
    volume

Terraform
    configuration
    remote state
    CI static checks
```

However, this did not address how application code associated with the Mercatura data platform will actually get from my Git repository and into Databricks reliably.

This issue is fundamentally different from provisioning infrastructure. Metaphorically, Terraform has built the foundations, the utilities, and locks on a building. This increment dealt with how an application is moved into that building, who can start the application, what environment it runs in, what data it may access, and how to prove that it works.

So, the objectives have graduated from infractucture deployment, to workload deployment.

---

## Comparing Terraform and Databricks Bundles

At the center of this increment is the distinction between Terraform and Databricks bundles.

#### Terraform

Terraform manages the underlying durable infrastructure and governance. For the current iteration of the Mercatura data platform this includes the management and governance of:

- Storage account
- containers
- Access Connector
- Azure RBAC
- Unity Catalog storage credential
- External locations
- Catalog
- Schema
- Volume
- Grants

Terraform builds and configures the platform.

#### Declarative Automation Bundles

Bundles manage Databricks application/workflow resources. In the context of the project this includes:

- Jobs
- Tasks
- Python wheel dependencies
- Deployment targets
- Runtime identity
- Workspace deployment 

Basically, Bundles manage the installation and configuration of an application on the platform. 

Both Terraform and Bundles are declarative systems, however they have ownership of different attributes of the overarching data platform product I am making.

To be very precise and brief, the definitions I use are:

- Terraform manages infrastructure delivery
- Bundles manage Databricks workload delivery
- Python wheel manages application delivery 

---

## Declarative Automation Bundles in More Detail

A bundle is basically a Databricks deployment definition. A bundle communicates with Databricks and provides it with information to execute a workload. A bundle at minimum describes things like the following:

- What the project is called
- What resource the project contains
- What code and/or artifacts to upload
- Which Databricks Workspace is to be used
- How the resources in the workspace should be configured

These descriptors are detailed in the `databricks.yml` file.

Bundles are somewhat similar in principle to things like Docker compose, Kubernetes YAML, Terraform HCL, or GitHub Actions YAML in the sense that the desired configuration is described in a file as opposed to manually clicking around options in a UI.

---

## Why Bundles Are Advantageous

Declaring the desired Databricks workflow configuration within a bundle YAML file removes the need to interact with the Databricks UI. Jobs can be created in the Databricks UI, and that approach still works. However, it is not very reproducible and appropriate for a production environment.

When doing anything with production level projects, it is important to fundamentally consider how traceable and reproducible a workflow is. Using bundles essentially codifies what has been done as part of a workflow, which can also be version controlled and reproduced. Hence, using Bundles allows me to know:

- who made changes to workflows
- what was a previous version of a configuration
- how I can reproduce the workload
- how I can review changes
- how I can deploy worklaods to another environment
- how the CI tests the workload

When the workload definition exists as a Bundle, this can be committed to the GitHub repository allowing someone to see the resource YAML, perform pull requests and commits, be able to Bundle plan and deploy the exact workload rather than emulating workflows directly in a UI.

Therefore, the UI in this circumstance is really an observation and debugging interface rather than serving as the source of truth.

---

## Python Wheel

It is completely possible just to upload application code to Databricks and run it. However, in real projects many modules, shored functions, package metadata, dependencies, versions, tests, and entry points may exist.

The python wheel serves as a standard installable Python package artifact. Basically, I wheel is a packaged and installable build of the Python project. 

This is contructed usgin `uv build --wheel` which creates a `.whl` file which can be installed into a job environment on Databricks as needed.

---

## Entry Points

In the `pyproject.toml` I have exposed entry points for the smoke tests at this stage with:

```toml
[project.scripts]
platform_smoke = "mercatura.platform.smoke:main"
catalog_smoke = "mercatura.platform.catalog_smoke:main"
```

Using entry points provides a stable application interface for Databricks to interact with and execute scripts. This is superior than just running some application code from some arbitrary file path, instead I install the mercatura package and run the desired entry point.

---

## The Direct Deployment Engine

Previously, Bundles used Terraform internally for some deployment behaviour but this approach has been retired. Now the modern Databricks Bundles use the direct deployment engine.

The direct engine communicates with Databricks using Databricks APIs/SDK rather than using the Terraform provider as the Bundle deployment mechanism.

When running `bundle deploy` this includes:

- the building of the Mercatura wheel
- uploading the wheel 
- uploading/synchronising Bundle source files
- comparing the bundle state (similar to Terraform states)
- creating and updating Databricks jobs
- recording the deployment state

Deploying is not just about uploading the databricks YAML, it actually does the application deployment operations.

---

## Serverless Jobs

Traditionally, Spark systems required a compute cluster to be configured. However, modern Spark systems have serverless compute capabilities.

Serverless compute means that I do not need to explicitly configure a Spark compute cluster. I have configured clusters in previous projects such as Hermes, so I have elected to use serverless to try something new and to change responsibility from cluster management to a larger focus on workflow management.

Serverless basically allows Databricks itself to make a judgement on the serverless environment a job should run in rather than me managing the cluster size, lifecycle, VM selection, and cluster termination policy.

---

## Service Principal

A service principal is just an identity that a service/software can use rather than a human developer.

I have an Entra ID Alexander and I interact as the user.

The service principal I made for CI automation was `sp-mercatura-github-dev` which is a machine identity, I dont physically use it.

Both my identity and the service principal (many service principals can be made) can have different scopes of permissions and different authorities across the platform, usually adherent to least privilege rules.

The service principal represents my automated deployment process, and is ultimately seperate from my own personal user identity.

---

## Why my personal Databricks Login was not used for GitHub

My databricks personal login is for me, and not for automation. If the CI automation used my personal identity, then the permissions would follow my broader personal account state, and the CI would have too much authority. Furthermore, seperating automation responsibilities from myself using service principle identities is generally cleaner and provides a very strict and clear responsibility boundary between me and what the automation ultimately manages.

---

## Not Using PATs

A Databricks PAT (or personal access token) could have been used for authorising the CI workflow to operate in Databricks. However, I did not do this since this would mean generating a secret that would need to be stored, rotated, protected, and revoked. Instead I am using federation and not having a long-lived Databricks PAT sit in GibHib secrets.

---

## OIDC

GitHub OIDC (OpenID Connect) is what I am using for GitHub - Databricks authorisation. In this use case, it is basically a way for GitHib to prove that it is the specific repository/workflow environment being run.

Instead of having GitHib store things like Azure passwords, I instead have:

- GitHub presents a short-lived signed identity proof
- Azure Entra ID validate it
- Entra issues temporary credentials

This avoids having secrets stored for long periods of time.

---

## Federated Credentials

The Microsoft Entra application contains a trust rule. Entra trusts OIDC assertions from GitHub given that they match the repository/environment identity.

GitHib itself does not receive the application password. Instead, Entra verifies whether the incoming GitHib OIDC token matches the trust condition.

GitHub was given `id-token: write` permission so the workflow was allowed to request its GitHib OIDC token. This token is ten presented to Entra.

The GitHub workflow uses Azure login with the application AI and the tenant ID and the GitHub OIDC token. Entra validates the federation and creates an authenticated Azure CLI session for the service principal to use. 

Furthermore, Databricks CLI also uses the authenticated Azure CLI/ Entra identity to authenticate to Azure Databricks.

The chain basically is GitHub:

- sends OIDC token to be verified by Entra
- Uses Azure login and an authenticated Azure CLI session is established for the service principal
- Uses Databricks CLI using Azure CLI / Entra identity to authenticate Databricks 
- Accesses the Databricks Workspace

Note that within Databricks the service principal was added to the workspace so Databricks could recognise it and apply the appropriate permissions to it.

---




