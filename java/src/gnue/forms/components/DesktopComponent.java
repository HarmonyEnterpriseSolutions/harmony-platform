package gnue.forms.components;

import javax.swing.JComponent;

public interface DesktopComponent {
	
	public FrameComponent[] getAllFrameComponents();
	
	/** may return null */
	public JComponent asComponent();
	
	public FrameComponent createFrameComponent(String title, boolean resizable, boolean closable, boolean maximizable, boolean iconifiable, Runnable onClose);


}
