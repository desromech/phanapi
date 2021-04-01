Extension { #name : #PhaNAPIGitHubRelease }

{ #category : #'*PhaNAPI-Iceberg' }
PhaNAPIGitHubRelease class >> fetchLibrary: libraryName fromIcebergRepoOfClass: class [
	^ self new fetchLibrary: libraryName fromIcebergRepoOfClass: class
]

{ #category : #'*PhaNAPI-Iceberg' }
PhaNAPIGitHubRelease >> fetchLibrary: libraryName fromIcebergRepoOfClass: class [
	| packageName iceRepo remote projectName tagName owner |
	packageName := class package name.
	iceRepo := IceRepository registry
		detect: [ :each | each includesPackageNamed: packageName ]
		ifFound: [ :repo | repo ]
		ifNone: [ ^ self error: 'Cannot download binary libraries from non-iceberg repo' ].

	remote := iceRepo origin.
	projectName := remote projectName.
	(PhaNAPI fullLibraryPathForCurrentPlatform: libraryName package: projectName) ifNotNil: [
		^ self
	].

	remote host = 'github.com' ifFalse: [ 
		^ self error: 'Cannot download automatically a library from a non-github repository.'
	].

	tagName := iceRepo head tags
		ifEmpty: [ nil ]
		ifNotEmpty: [ :tags | tags first name ].
	owner := remote owner.
	
	^ self fetchLibrary: libraryName fromUser: owner repository: projectName release: tagName
]
