import unittest

def exercise_scenarios():
    import importlib.util,tempfile,subprocess,json,fcntl
    from pathlib import Path
    spec=importlib.util.spec_from_file_location('updater',str(Path(__file__).resolve().parents[1]/'scripts/update.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    with tempfile.TemporaryDirectory(prefix='cadcraft-updater-tests-') as td:
     root=Path(td);m.ROOT=root;m.UPDATES=root/'updates';m.UPDATES.mkdir();m.CONFIG=root/'config.json';m.ACTIVE=root/'active.json';m.BINARY=root/'cadcraft';m.PREFS=root/'app.ron';m.WINDOW_LOCK=root/'window.lock'
     source=m.UPDATES/'source';source.mkdir()
     def git(*a):return subprocess.check_output(['git','-c','user.name=Updater Fixture','-c','user.email=fixture@invalid',*a],cwd=source,stderr=subprocess.DEVNULL)
     git('init');(source/'base.txt').write_text('original\n');git('add','.');git('commit','-m','fixture');git('tag','v1.0.0')
     (source/'base.txt').write_text('custom\n');(source/'copilot.rs').write_text('copilot fixture\n');before=git('diff','--cached')
     dest=root/'snapshot';dest.mkdir();patch=m.snapshot(source,dest);assert git('diff','--cached')==before
     assert 'copilot.rs' in patch.read_text() and 'custom' in patch.read_text()
     first=m.fingerprint(source);(source/'copilot.rs').write_text('changed fixture\n');assert m.fingerprint(source)!=first
     # A failed check must mark the build failed and leave the installed program untouched.
     m.BINARY.write_bytes(b'old executable');m.PREFS.write_text('original settings');config={'source':str(source),'target':str(root/'target'),'toolchain':'/usr/bin'}
     logs=root/'logs';logs.mkdir();state={'stage':'prepared','logs':str(logs),'tag':'v1.0.0','tagObject':'abc','source':str(source)};m.write(m.state_path(source),state);m.write(m.CONFIG,config);m.write(m.ACTIVE,{'tag':'old'})
     original_command=m.command
     def fail_cargo(argv,*a,**kw):
      if argv[0]=='cargo':raise RuntimeError('intentional test failure')
      return original_command(argv,*a,**kw)
     m.command=fail_cargo
     try:m.build(config,dict(),source);raise AssertionError('build should fail')
     except RuntimeError as e:assert 'intentional' in str(e)
     finally:m.command=original_command
     assert m.read(m.state_path(source))['stage']=='failed' and m.BINARY.read_bytes()==b'old executable'
     # Verified manifest and a valid hash are required; running-window lock refuses installation.
     artifact=logs/'candidate';artifact.write_bytes(b'new executable');state.update(stage='verified',artifact=str(artifact),sha256=m.digest(artifact),fingerprint=m.fingerprint(source));m.write(m.state_path(source),state)
     with m.WINDOW_LOCK.open('a') as lock:
      fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
      try:m.install(config,source);raise AssertionError('running-window lock ignored')
      except RuntimeError:pass
     assert m.BINARY.read_bytes()==b'old executable'
     artifact.write_bytes(b'tampered')
     try:m.install(config,source);raise AssertionError('hash check ignored')
     except RuntimeError:pass
     artifact.write_bytes(b'new executable');m.install(config,source);assert m.BINARY.read_bytes()==b'new executable'
     m.PREFS.write_text('newer user settings');m.rollback(config);assert m.BINARY.read_bytes()==b'old executable' and m.PREFS.read_text()=='newer user settings'
     # Exercise the actual clone/fetch/three-way preparation against a local release fixture.
     upstream=root/'upstream'
     subprocess.run(['git','clone','--no-local',str(source),str(upstream)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
     def upstream_git(*args):return subprocess.check_output(['git','-c','user.name=Updater Fixture','-c','user.email=fixture@invalid',*args],cwd=upstream,stderr=subprocess.DEVNULL)
     (upstream/'upstream.txt').write_text('new upstream feature\n');upstream_git('add','.');upstream_git('commit','-m','compatible release');upstream_git('tag','v1.1.0')
     m.UPSTREAM=str(upstream);tag,sha=m.latest(dict());assert tag=='v1.1.0'
     old_head=git('rev-parse','HEAD');stage=m.prepare(config,dict(),tag,sha)
     assert (stage/'base.txt').read_text()=='custom\n' and (stage/'upstream.txt').exists() and (stage/'copilot.rs').exists()
     assert git('rev-parse','HEAD')==old_head and (source/'base.txt').read_text()=='custom\n'
     (upstream/'base.txt').write_text('conflicting upstream change\n');upstream_git('add','.');upstream_git('commit','-m','conflicting release');upstream_git('tag','v1.2.0')
     tag,sha=m.latest(dict())
     try:m.prepare(config,dict(),tag,sha);raise AssertionError('conflict should stop prepare')
     except RuntimeError as error:assert '冲突' in str(error)
     pending=m.read(root/'updater/pending.json');assert m.read(m.state_path(Path(pending['source'])))['stage']=='conflict'
     assert m.BINARY.read_bytes()==b'old executable'
    print('PASS: isolated snapshots preserve index, source mutation detection, failed gate preserves installation, running-window lock, artifact hash, install backup and rollback without replacing newer preferences, stable tag discovery, real compatible prepare and conflict isolation')

class UpdaterTests(unittest.TestCase):
    def test_merge_install_and_rollback_safety(self):
        exercise_scenarios()

if __name__ == "__main__":
    unittest.main()
