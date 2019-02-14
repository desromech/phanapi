"
I provide some commmon utilities for downloading libraries from a specific cloud storage provider.
"
Class {
	#name : #PhaNAPIWebBinaryRepository,
	#superclass : #Object,
	#category : #'PhaNAPI-Core-BinaryRepository'
}

{ #category : #bintray }
PhaNAPIWebBinaryRepository >> doHTTPRequest: aBlock withProgress: progressName [
	| result |
	UIManager default informUserDuring: [ :bar |
		bar label: progressName.
		[
			result := aBlock value
		] on: HTTPProgress do: [ :progress |
			progress isEmpty ifFalse: [ 
				bar current: progress percentage
			].
			progress resume
		]
	].

	^ result
	
]

{ #category : #'web requests' }
PhaNAPIWebBinaryRepository >> requestJSON: uri [
	^ self requestJSON: uri progressName: 'Requesting web binary repository metadata...'
]

{ #category : #'web requests' }
PhaNAPIWebBinaryRepository >> requestJSON: uri progressName: progressName [
	^ self doHTTPRequest: [NeoJSONReader fromString: (ZnClient new
		beOneShot;
		signalProgress: true;
		get: uri) contents
	] withProgress: progressName
]
