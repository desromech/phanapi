Class {
	#name : #PhaNAPIWebBinaryRepository,
	#superclass : #Object,
	#category : #'PhaNAPI-Core-BinaryRepository'
}

{ #category : #directories }
PhaNAPIWebBinaryRepository >> downloadsDirectory [
	^ self phanapiDirectory / #downloads
]

{ #category : #directories }
PhaNAPIWebBinaryRepository >> phanapiDirectory [
	^ FileLocator localDirectory / #phanapi
]

{ #category : #bintray }
PhaNAPIWebBinaryRepository >> requestJSON: uri [
	^ self doHTTPRequestWithProgress: [NeoJSONReader fromString: (ZnClient new
		beOneShot;
		signalProgress: true;
		get: uri) contents]
]
