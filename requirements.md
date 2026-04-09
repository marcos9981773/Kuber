# Kuber

## About

Kuber is a tool for managing Kubernetes clusters. It provides a simple and intuitive interface for deploying and managing applications on Kubernetes. Is a desktop application.

## Build Requirements

Python 3.13+
QT 4.11+
Kubernetes 1.27+
Docker 20.10+
Git 2.39+

## Frameworks and Libraries
1. PyQt5: A set of Python bindings for the Qt application framework, used for building the user interface of Kuber.


## APP Requirements

1. Load kubernetes config file from user default location "${HOME}\.kube\config"
2. Ensure that the user has the necessary permissions to access and modify Kubernetes resources
3. Verify that the user has a working internet connection for pulling Docker images and accessing Kubernetes API
4. Check that the user has a compatible version of Docker installed and running
5. Validate that the user has a valid Git configuration and access to the required repositories

## User experience requirements

1. User friendly interface
2. Clear and concise error messages
3. Responsive design for different screen sizes
4. Accessibility features for users with disabilities
5. Support for multiple languages and translations
6. Support for dark mode
7. Support for high contrast mode
8. Support for keyboard navigation
9. Support for screen readers
10. Support for touch screen devices

## Features

1. Cluster management: Kuber allows users to easily manage multiple Kubernetes clusters from a single interface. Users can view cluster status, switch between clusters, and perform cluster operations such as scaling and upgrading.
2. Application deployment:
   1. Deploy applications to Kubernetes clusters using Docker images.
   2. Support for deploying applications using Helm charts.
   3. Support for deploying applications using Kubernetes manifests.
3. Resource management: Kuber provides a visual interface for managing Kubernetes resources such as pods, services, deployments, and config maps. Users can view resource details, edit resource configurations, and perform resource operations such as scaling and rolling updates.
4. Monitoring and logging: Kuber integrates with Kubernetes monitoring and logging tools to provide real-time insights into cluster and application performance. Users can view metrics, logs, and events for their clusters and applications.
5. User management: Kuber allows users to manage access to Kubernetes clusters and resources. Users can create and manage user accounts, assign roles and permissions, and view audit logs for user activity.
6. Backup and restore: Kuber provides a backup and restore feature for Kubernetes clusters. Users can create backups of their cluster configurations and data, and restore them in case of disasters or data loss.
7. Openshift support: Kuber provides support for managing OpenShift clusters, allowing users to deploy and manage applications on OpenShift using the same interface as Kubernetes.
8. Multi-cloud support: Kuber allows users to manage Kubernetes clusters across multiple cloud providers, providing a unified interface for managing clusters regardless of their underlying infrastructure.
9. Custom resource support: Kuber provides support for managing custom resources in Kubernetes, allowing users to create and manage their own resource types and integrate them into the Kuber interface.
